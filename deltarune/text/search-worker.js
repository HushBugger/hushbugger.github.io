"use strict";

importScripts("rendered.json.js");

/**
 * @typedef {{
 *      chap: "all" | "1" | "2" | "3" | "4";
 *      lang: "en" | "ja" | "both";
 *  }} Config
 *
 * @typedef {[string | null, boolean, number, number]} Message
 * @typedef {{ en: Message; ja: Message; }} MessagePair
 * @typedef {Record<string, MessagePair>} RenderedSection
 * @typedef {Record<string, RenderedSection>} RenderedChapter
 * @typedef {Record<string, RenderedChapter>} Rendered
 * @typedef {{
 *      query: string;
 *      config: Config;
 *      generation: number;
 *  }} SearchQuery
 * @typedef {[number, number]} Span
 * @typedef {[string, string, string]} Path
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

/** @type {Rendered} */
// @ts-ignore
const munged = rendered;

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
        .replace(/&amp;/g, "&");
}

for (const chap of Object.keys(munged)) {
    for (const section of Object.keys(munged[chap])) {
        for (const msgid of Object.keys(munged[chap][section])) {
            if (munged[chap][section][msgid].en[0]) {
                munged[chap][section][msgid].en[0] = munge(munged[chap][section][msgid].en[0]);
            }
            if (munged[chap][section][msgid].ja[0]) {
                munged[chap][section][msgid].ja[0] = munge(munged[chap][section][msgid].ja[0]);
            }
        }
    }
}

let currentGen = 0;

/** @param {MessageEvent<SearchQuery>} event */
onmessage = function (event) {
    if (event.data.generation < currentGen) {
        return;
    }
    currentGen = event.data.generation;
    setTimeout(function () {
        doSearch(event.data);
    }, 0);
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

    let rawPattern = "";
    for (const char of query.query) {
        // RegExp.escape() is too modern.
        // AFAICT this is good enough for our purposes.
        if (".*+?^${}()|[]\\".includes(char)) {
            rawPattern += "\\" + char;
        } else if (char === " ") {
            rawPattern += "[ \n\u3000]+";
        } else {
            rawPattern += char;
        }
    }
    const pattern = new RegExp(rawPattern, "ig");

    for (const chap of Object.keys(munged)) {
        if (query.config.chap !== "all" && query.config.chap !== chap) {
            continue;
        }
        for (const section of Object.keys(munged[chap])) {
            for (const msgid of Object.keys(munged[chap][section])) {
                const msg = munged[chap][section][msgid];
                if (
                    query.config.lang !== "ja" &&
                    msg.en[0] &&
                    !(msg.en[1] && query.config.chap === "all")
                ) {
                    /** @type {Span[]} */
                    const spans = [];
                    for (const match of msg.en[0].matchAll(pattern)) {
                        spans.push([match.index, match.index + match[0].length]);
                    }
                    if (spans.length) {
                        results.results.push({
                            path: [chap, section, msgid],
                            lang: "en",
                            spans: spans,
                        });
                    }
                }
                if (
                    query.config.lang !== "en" &&
                    msg.ja[0] &&
                    !(msg.ja[1] && query.config.chap === "all")
                ) {
                    /** @type {Span[]} */
                    const spans = [];
                    for (const match of msg.ja[0].matchAll(pattern)) {
                        spans.push([match.index, match.index + match[0].length]);
                    }
                    if (spans.length) {
                        results.results.push({
                            path: [chap, section, msgid],
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
