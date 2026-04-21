"use strict";

/**
 * @typedef {{
 *      chap: "all" | "1" | "2" | "3" | "4";
 *      lang: "en" | "ja" | "both";
 *  }} Config
 *
 * @typedef {{
 *      meta: {"msgid": number, "en": number, "ja": number, "count": number};
 *      groups: Record<"1"|"2"|"3"|"4", Record<string, number[]>>;
 *  }} GroupIndex
 *
 * @typedef {{
 *      type: 'init';
 *      rawText: string;
 *      index: GroupIndex;
 *  }} SearchInit
 * @typedef {{
 *      type: 'query';
 *      query: RegExp;
 *      config: Config;
 *      generation: number;
 *  }} SearchQuery
 * @typedef {[number, number]} Span
 * @typedef {[string, string, number]} Path
 * @typedef {{
 *      path: Path;
 *      lang: 'en' | 'ja';
 *      spans: Span[];
 *  }} Result
 * @typedef {{
 *      generation: number;
 *      results: Result[];
 *  }} ResultList
 */

/** @type {string} */
let rawText;

/** @type {GroupIndex} */
let index;

const MSG_SIZE = 21;

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
    } else if (width === 2) {
        return function (idx) {
            return (
                rawText.charCodeAt(idx * MSG_SIZE + offset) +
                rawText.charCodeAt(idx * MSG_SIZE + offset + 1) * 128
            );
        };
    } else {
        return function (idx) {
            return (
                rawText.charCodeAt(idx * MSG_SIZE + offset) +
                rawText.charCodeAt(idx * MSG_SIZE + offset + 1) * 128 +
                rawText.charCodeAt(idx * MSG_SIZE + offset + 2) * 16384
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
const sourceOffFor = mkExtractor(3);
const sourceLenFor = mkExtractor(1);
const dupFor = mkExtractor(1);
const nhenFor = mkExtractor(1);
const whenFor = mkExtractor(1);
const nhjaFor = mkExtractor(1);
const whjaFor = mkExtractor(1);

/** @param {number} idx */
function msgidFor(idx) {
    const off = index.meta.msgid + msgidOffFor(idx);
    return rawText.slice(off, off + msgidLenFor(idx));
}

/** @param {number} idx */
function enFor(idx) {
    const off = index.meta.en + enOffFor(idx);
    return rawText.slice(off, off + enLenFor(idx));
}

/** @param {number} idx */
function jaFor(idx) {
    const off = index.meta.ja + jaOffFor(idx);
    return rawText.slice(off, off + jaLenFor(idx));
}

/** @type {string[]} */
const munged = [];

/** @param {SearchInit} data */
function init(data) {
    if (rawText || munged.length) {
        throw new Error("double init");
    }

    rawText = data.rawText;
    index = data.index;

    /**
     * @param {string} text
     * @return {string}
     */
    function munge(text) {
        return text
            .replace(/<[^>]*(?:alt="([^>"]*)")[^>]*>/g, function (_match, p1) {
                return p1 || "";
            })
            .replace(/<[^>]*>/g, "")
            .replace(/&gt;/g, ">")
            .replace(/&lt;/g, "<")
            .replace(/&amp;/g, "&")
            .replace(/！/g, "!")
            .replace(/？/g, "?")
            .replace(/＊/g, "*")
            .replace(/\s+/g, " ");
    }

    for (let msgIdx = 0; msgIdx < index.meta.count; msgIdx++) {
        munged.push(munge(enFor(msgIdx)));
        munged.push(munge(jaFor(msgIdx)));
    }

    if (pending) {
        pending();
        pending = null;
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

    /** @type {ResultList} */
    const results = {
        generation: query.generation,
        results: [],
    };

    for (const chap of /** @type {const} */ (["1", "2", "3", "4"])) {
        if (query.config.chap !== "all" && query.config.chap !== chap) {
            continue;
        }
        for (const groupName of Object.keys(index.groups[chap])) {
            const group = index.groups[chap][groupName];
            for (let msgIdx = group[0]; msgIdx < group[0] + group[1]; msgIdx++) {
                if (
                    query.config.lang !== "ja" &&
                    munged[msgIdx * 2] &&
                    !(dupFor(msgIdx) & 1 && query.config.chap === "all")
                ) {
                    /** @type {Span[]} */
                    const spans = [];
                    for (const match of munged[msgIdx * 2].matchAll(query.query)) {
                        spans.push([match.index, match.index + match[0].length]);
                    }
                    if (spans.length) {
                        results.results.push({
                            path: [chap, groupName, msgIdx],
                            lang: "en",
                            spans: spans,
                        });
                    }
                }
                if (
                    query.config.lang !== "en" &&
                    munged[msgIdx * 2 + 1] &&
                    !(dupFor(msgIdx) & 2 && query.config.chap === "all")
                ) {
                    /** @type {Span[]} */
                    const spans = [];
                    for (const match of munged[msgIdx * 2 + 1].matchAll(query.query)) {
                        spans.push([match.index, match.index + match[0].length]);
                    }
                    if (spans.length) {
                        results.results.push({
                            path: [chap, groupName, msgIdx],
                            lang: "ja",
                            spans: spans,
                        });
                    }
                }
            }
        }
    }

    setTimeout(function () {
        if (query.generation < currentGen) {
            return;
        }
        postMessage(results);
    }, 0);
}
