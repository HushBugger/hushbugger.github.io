"use strict";

/**
 * @typedef {'1' | '2' | '3' | '4'} Chapter
 *
 * @typedef {{
 *      chap: "all" | Chapter;
 *      lang: "en" | "ja" | "both";
 *  }} Config
 *
 * @typedef {{
 *      count: number;
 *      ranges: Record<Config['chap'], [number, number]>;
 *      msgidOff: number;
 *      enOff: number;
 *      jaOff: number;
 *  }} Meta
 *
 * @typedef {{
 *      type: 'init';
 *      rawText: string;
 *  }} SearchInit
 * @typedef {{
 *      type: 'query';
 *      query: RegExp;
 *      config: Config;
 *      generation: number;
 *  }} SearchQuery
 * @typedef {number} Result
 * @typedef {{
 *      generation: number;
 *      results: Result[];
 *  }} ResultList
 */

/** @type {string} */
let rawText;

/** @type {Meta} */
let meta;

const MSG_SIZE = 17;

let curMsgOffset = 0;

/**
 * @param {1|2|3} width
 * @return {(idx: number) => number}
 */
function mkExtractor(width) {
    const offset = curMsgOffset;
    curMsgOffset += width;
    if (width === 1) {
        return function (idx) {
            return rawText.charCodeAt(idx * MSG_SIZE + offset);
        };
    } else {
        return function (idx) {
            return (
                rawText.charCodeAt(idx * MSG_SIZE + offset) +
                rawText.charCodeAt(idx * MSG_SIZE + offset + 1) * 128 +
                rawText.charCodeAt(idx * MSG_SIZE + offset + 2) * 128 * 128
            );
        };
    }
}

const msgidOffFor = mkExtractor(3);
const msgidLenFor = mkExtractor(1);
const enOffFor = mkExtractor(3);
const enLenFor = mkExtractor(1);
const jaOffFor = mkExtractor(3);
const jaLenFor = mkExtractor(1);
const dupFor = mkExtractor(1);
const nhenFor = mkExtractor(1);
const whenFor = mkExtractor(1);
const nhjaFor = mkExtractor(1);
const whjaFor = mkExtractor(1);

/** @param {number} idx */
function msgidFor(idx) {
    const off = meta.msgidOff + msgidOffFor(idx);
    return rawText.slice(off, off + msgidLenFor(idx));
}

/** @param {number} idx */
function enFor(idx) {
    const off = meta.enOff + enOffFor(idx);
    return rawText.slice(off, off + enLenFor(idx));
}

/** @param {number} idx */
function jaFor(idx) {
    const off = meta.jaOff + jaOffFor(idx);
    return rawText.slice(off, off + jaLenFor(idx));
}

/**
 * @param {Config} config
 * @param {number} start
 * @param {number} end
 * @param {(idx: number, kind: 1|2|3|4, chap: Chapter) => void | true} callback
 */
function iterText(config, start, end, callback) {
    start = Math.max(start, meta.ranges[config.chap][0]);
    const chapEnd = meta.ranges[config.chap][1];
    end = Math.min(end, chapEnd);

    /** @type {number | null} */
    let pendingHeader = null;
    /** @type {Chapter} */
    let chap = "1";
    for (
        let idx = start;
        // Nasty case: if a header is at the end of the range we have to keep looking
        // to decide whether to render it
        idx < end || (pendingHeader !== null && end < chapEnd);
        idx++
    ) {
        if (chap === "1" && idx >= meta.ranges[1][1]) {
            chap = "2";
        }
        if (chap === "2" && idx >= meta.ranges[2][1]) {
            chap = "3";
        }
        if (chap === "3" && idx >= meta.ranges[3][1]) {
            chap = "4";
        }
        const dup = dupFor(idx);
        if (dup & 4) {
            if (idx >= end) {
                return;
            }
            if (!msgidFor(idx)) {
                // chapter header
                if (callback(idx, 4, chap)) {
                    return;
                }
                pendingHeader = null;
            } else {
                // section header, only output if section has children
                pendingHeader = idx;
            }
            continue;
        }

        let kind = 0;
        if (config.lang === "en") {
            if (!(dup & 1 && config.chap === "all") && enLenFor(idx)) {
                kind |= 1;
            }
        } else if (config.lang === "ja") {
            if (!(dup & 2 && config.chap === "all") && jaLenFor(idx)) {
                kind |= 2;
            }
        } else if (config.lang === "both") {
            if (!((dup & 3) === 3 && config.chap === "all")) {
                if (enLenFor(idx)) {
                    kind |= 1;
                }
                if (jaLenFor(idx)) {
                    kind |= 2;
                }
            }
        }

        if (kind) {
            if (pendingHeader !== null) {
                if (callback(pendingHeader, 4, chap)) {
                    return;
                }
                pendingHeader = null;
            }
            if (idx >= end) {
                return;
            }
            if (callback(idx, /** @type {1|2|3} */ (kind), chap)) {
                return;
            }
        }
    }
}

/** @type {string[]} */
const munged = [];

/** @param {SearchInit} data */
function init(data) {
    if (rawText || munged.length) {
        throw new Error("double init");
    }

    rawText = data.rawText;
    meta = JSON.parse(rawText.slice(rawText.lastIndexOf("\0") + 1));

    if (pending) {
        pending();
        pending = null;
    }
}

let preprocessed = { en: false, ja: false };

/** @param {'en' | 'ja'} lang */
function preprocess(lang) {
    const offset = lang === "en" ? 0 : 1;
    if (preprocessed[lang]) {
        return;
    }
    preprocessed[lang] = true;

    const normalizeMap = new Map([
        ["！", "!"],
        ["？", "?"],
        ["＊", "*"],
        ["。", "."],
        ["～", "~"],
        ["：", ":"],
        ["（", "("],
        ["）", ")"],
        ["…", "..."],
        ["&gt;", ">"],
        ["&lt;", "<"],
        ["&amp;", "&"],
        // Out of the characters we normalize for search inputs only these
        // occur in the game text
        ["\u2019", "'"],
        ["\u201C", '"'],
        ["\u201D", '"'],
    ]);

    /**
     * @param {string} text
     * @return {string}
     */
    function munge(text) {
        return text.replace(
            /<[^>]*>|[ \n\u3000]{2,}|[\n\u3000]|&gt;|&lt;|&amp;|[！？＊。～：（）“”’…]/g,
            function (match) {
                if (match[0] === "<") {
                    const altIdx = match.indexOf('alt="');
                    if (altIdx !== -1) {
                        return match.slice(altIdx + 5).split('"')[0];
                    }
                    return "";
                }
                return normalizeMap.get(match) || " ";
            }
        );
    }

    for (let msgIdx = 0; msgIdx < meta.count; msgIdx++) {
        if (offset === 1 && !preprocessed.en && dupFor(msgIdx) & 4) {
            munged[msgIdx * 2] = munge(enFor(msgIdx));
        }
        munged[msgIdx * 2 + offset] = munge(offset ? jaFor(msgIdx) : enFor(msgIdx));
    }
}

let currentGen = 0;

/** @type {null | (() => void)} */
let pending = null;

/** @param {MessageEvent<SearchQuery | SearchInit>} event */
onmessage = function (event) {
    const data = event.data;
    if (data.type === "init") {
        init(data);
        return;
    }
    if (data.generation < currentGen) {
        return;
    }
    currentGen = data.generation;
    if (!rawText) {
        // Received messages out of order?!
        pending = function () {
            doSearch(data);
        };
    } else {
        setTimeout(function () {
            doSearch(data);
        }, 0);
    }
};

/** @param {SearchQuery} query */
function doSearch(query) {
    if (query.generation < currentGen) {
        return;
    }

    if (query.config.lang !== "ja") {
        preprocess("en");
    }
    if (query.config.lang !== "en") {
        preprocess("ja");
    }

    /** @type {ResultList} */
    const results = {
        generation: query.generation,
        results: [],
    };

    iterText(query.config, ...meta.ranges[query.config.chap], function (idx, kind) {
        if ((kind === 4 || kind & 1) && munged[idx * 2].search(query.query) !== -1) {
            results.results.push(idx * 2);
        }
        if (kind & 2 && munged[idx * 2 + 1].search(query.query) !== -1) {
            results.results.push(idx * 2 + 1);
        }
    });

    setTimeout(function () {
        if (query.generation < currentGen) {
            return;
        }
        postMessage(results);
    }, 0);
}
