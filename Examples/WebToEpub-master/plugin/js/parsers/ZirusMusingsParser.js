/*
  Parses the Lazy Dungeon Master story on https://zirusmusings.com/ldm-ch84/
*/
"use strict";

parserFactory.register("zirusmusings.com", function() { return new ZirusMusingsParser() });

class ZirusMusingsParser extends Parser {
    constructor() {
        super();
    }

    getChapterUrls(dom) {
        let that = this;
        let content = that.findContent(dom);

        let getChapterArc = undefined;
        if (dom.baseURI === "https://zirusmusings.com/ldm-toc/") {
            getChapterArc = that.getChapterArc;
        } 
        let chapters = util.hyperlinksToChapterList(content, that.isChapterHref, getChapterArc);
        return Promise.resolve(chapters);
    }

    isChapterHref(link) {
        let hostname = link.hostname;
        return (hostname === "pirateyoshi.wordpress.com") ||
            (hostname === "zirusmusings.com") ||
            (hostname === "imgur.com");
    }

    getChapterArc(link) {
        let arc = null;
        if (link.parentNode !== null) {
            let parent = link.parentNode;
            if (parent.tagName === "P") {
                let strong = parent.querySelector("strong");
                if (strong != null) {
                    arc = strong.innerText;
                };
            };
        };
        return arc;
    }

    extractTitle(dom) {
        return dom.querySelector("meta[property='og:title']").getAttribute("content");
    }

    // find the node(s) holding the story content
    findContent(dom) {
        return dom.querySelector("article:not(.comment-body) div.entry-content");
    }

    removeUnwantedElementsFromContentElement(element) {
        super.removeUnwantedElementsFromContentElement(element);

        // remove the previous | TOC | Next hyperlinks
        let toc = this.findTocElement(element);
        if (toc !== null) {
            toc.parentNode.remove();
        };
    }

    findTocElement(div) {
        return div.querySelector("a[href*='toc/']");
    }
}
