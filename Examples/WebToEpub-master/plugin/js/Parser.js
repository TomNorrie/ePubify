/*
  Base class that all parsers build from.
*/
"use strict";

class Parser {
    constructor(imageCollector) {
        this.chapters = [];
        this.imageCollector = imageCollector || new ImageCollector();
        this.userPreferences = null;
        this.chapterListUrl = null;
    }

    copyState(otherParser) {
        this.chapters = otherParser.chapters;
        this.imageCollector.copyState(otherParser.imageCollector);
        this.userPreferences = otherParser.userPreferences;
        this.chapterListUrl = otherParser.chapterListUrl;
    }

    onUserPreferencesUpdate(userPreferences) {
        this.userPreferences = userPreferences;
        this.imageCollector.onUserPreferencesUpdate(userPreferences);
    }

    isChapterPackable(chapter) {
        return (chapter.rawDom != null) && (chapter.isIncludeable);
    }

    convertRawDomToContent(chapter) {
        let that = this;
        let content = that.findContent(chapter.rawDom);
        that.customRawDomToContentStep(chapter, content);
        that.removeUnwantedElementsFromContentElement(content);
        this.addTitleToContent(chapter, content);
        util.fixBlockTagsNestedInInlineTags(content);
        that.imageCollector.replaceImageTags(content);
        util.removeUnusedHeadingLevels(content);
        util.removeUnneededIds(content);
        util.makeHyperlinksRelative(chapter.rawDom.baseURI, content);
        util.setStyleToDefault(content);
        util.prepForConvertToXhtml(content);
        util.removeEmptyDivElements(content);
        util.removeTrailingWhiteSpace(content);
        if (util.isElementWhiteSpace(content)) {
            let errorMsg = chrome.i18n.getMessage("warningNoVisibleContent", [chapter.sourceUrl]);
            ErrorLog.showErrorMessage(errorMsg);
        }
        return content;
    }

    addTitleToContent(chapter, content) {
        let title = this.findChapterTitle(chapter.rawDom);
        if (title !== null) {
            content.insertBefore(title, content.firstChild);
        };
    }

    /**
     * Element with title of an individual chapter
     * Override when chapter title not in content element
    */
    findChapterTitle(dom) {   // eslint-disable-line no-unused-vars
        return null;
    }

    removeUnwantedElementsFromContentElement(element) {
        util.removeScriptableElements(element);
        util.removeComments(element);
        util.removeElements(element.querySelectorAll("noscript, input"));
        util.removeUnwantedWordpressElements(element);
        util.removeMicrosoftWordCrapElements(element);
        util.removeShareLinkElements(element);
        this.removeNextAndPreviousChapterHyperlinks(element);
        util.removeLeadingWhiteSpace(element);
    };

    customRawDomToContentStep(chapter, content) { // eslint-disable-line no-unused-vars
        // override for any custom processing
    }

    populateUI(dom) {
        this.getFetchContentButton().onclick = this.onFetchChaptersClicked.bind(this);
        document.getElementById("packRawButton").onclick = this.packRawChapters.bind(this);
        let coverUrl = this.findCoverImageUrl(dom);
        if (!util.isNullOrEmpty(coverUrl)) {
            CoverImageUI.setCoverImageUrl(coverUrl);
        };
    }

    /**
     * Default implementation, take first image in content section
    */
    findCoverImageUrl(dom) {
        if (dom != null) {
            let content = this.findContent(dom);
            if (content != null) {
                let cover = content.querySelector("img");
                if (cover != null) {
                    return cover.src;
                };
            };
        };
        return null;
    }

    removeNextAndPreviousChapterHyperlinks(element) {
        if (this.findParentNodeOfChapterLinkToRemoveAt != null) {
            let that = this;
            let chapterLinks = new Set();
            for(let c of that.chapters) { 
                chapterLinks.add(util.normalizeUrl(c.sourceUrl));
            };

            for(let unwanted of util.getElements(element, "a", link => chapterLinks.has(util.normalizeUrl(link.href)))
                .map(link => that.findParentNodeOfChapterLinkToRemoveAt(link))) {
                unwanted.remove();
            };
        }
    }

    /**
    * default implementation turns each chapter into single epub item
    */
    chapterToEpubItems(chapter, epubItemIndex) {
        let content = this.convertRawDomToContent(chapter);
        let items = [];
        if (content != null) {
            items.push(new ChapterEpubItem(chapter, content, epubItemIndex));
        }
        return items;
    }

    /**
    * default implementation, use the <title> element
    */
    extractTitle(dom) {
        return dom.title.trim();
    };

    /**
    * default implementation
    */
    extractAuthor(dom) {  // eslint-disable-line no-unused-vars
        return "<unknown>";
    }

    /**
    * default implementation, a number of sites use jetpack tags
    * but if not available, default to English
    */
    extractLanguage(dom) {
        let locale = dom.querySelector("meta[property='og:locale']");
        return (locale === null) ? "en" : locale.getAttribute("content");
    }

    /**
    * default implementation, Derived classes will override
    */
    extractSeriesInfo(dom, metaInfo) {  // eslint-disable-line no-unused-vars
    }

    getEpubMetaInfo(dom){
        let that = this;
        let metaInfo = new EpubMetaInfo();
        metaInfo.uuid = dom.baseURI;
        metaInfo.title = that.extractTitle(dom);
        metaInfo.author = that.extractAuthor(dom);
        metaInfo.language = that.extractLanguage(dom);
        metaInfo.fileName = that.makeSaveAsFileNameWithoutExtension(metaInfo.title);
        that.extractSeriesInfo(dom, metaInfo);
        return metaInfo;
    }

    singleChapterStory(baseUrl, dom) {
        return [{
            sourceUrl: baseUrl,
            title: this.extractTitle(dom)
        }];
    }

    getBaseUrl(dom) {
        return Array.prototype.slice.apply(dom.getElementsByTagName("base"))[0].href;
    }

    makeSaveAsFileNameWithoutExtension(title) {
        return (title == null)  ? "web" : util.safeForFileName(title);
    }

    epubItemSupplier() {
        let that = this;
        let epubItems = that.chaptersToEpubItems(that.chapters);
        let supplier = new EpubItemSupplier(this, epubItems, that.imageCollector);
        return supplier;
    }

    chaptersToEpubItems(chapters) {
        let epubItems = [];
        let index = 0;
        let initialHostName = this.initialHostName();

        for(let chapter of chapters.filter(c => this.isChapterPackable(c))) {
            let pageParser = this.parserForChapter(initialHostName, chapter);
            let newItems = pageParser.chapterToEpubItems(chapter, index);
            epubItems = epubItems.concat(newItems);
            index += newItems.length;
            delete(chapter.rawDom);
        }
        return epubItems;
    }

    // called when plugin has obtained the first web page
    onLoadFirstPage(url, firstPageDom) {
        let that = this;
        this.chapterListUrl = url;
        
        // returns promise, because may need to fetch additional pages to find list of chapters
        that.getChapterUrls(firstPageDom).then(function(chapters) {
            if (that.userPreferences.chaptersPageInChapterList.value) {
                chapters = that.addFirstPageUrlToChapters(url, firstPageDom, chapters);
            }
            chapters = that.cleanChaperListUrls(chapters);
            let chapterUrlsUI = new ChapterUrlsUI(that);
            chapterUrlsUI.populateChapterUrlsTable(chapters);
            if (0 < chapters.length) {
                if (chapters[0].sourceUrl === url) {
                    chapters[0].rawDom = firstPageDom;
                    that.updateLoadState(chapters[0]);
                }
                that.getProgressBar().value = 0;
            }
            that.chapters = chapters;
            chapterUrlsUI.connectButtonHandlers();
        }).catch(function (err) {
            ErrorLog.showErrorMessage(err);
        });
    }

    cleanChaperListUrls(chapters) {
        let foundUrls = new Set();
        let isUnique = function(chapterInfo) {
            let unique = !foundUrls.has(chapterInfo.sourceUrl);
            if (unique) {
                foundUrls.add(chapterInfo.sourceUrl);
            }
            return unique;
        }

        return chapters
            .map(this.fixupImgurGalleryUrl)
            .filter(isUnique);
    }

    fixupImgurGalleryUrl(chapter) {
        chapter.sourceUrl = Imgur.fixupImgurGalleryUrl(chapter.sourceUrl);
        return chapter;
    }

    addFirstPageUrlToChapters(url, firstPageDom, chapters) {
        let present = chapters.find(e => e.sourceUrl === url);
        if (present)
        {
            return chapters;
        } else {
            return [{
                sourceUrl:  url,
                title: this.extractTitle(firstPageDom)
            }].concat(chapters);
        }
    }

    onFetchChaptersClicked() {
        if (0 == this.chapters.length) {
            ErrorLog.showErrorMessage(chrome.i18n.getMessage("noChaptersFoundAndFetchClicked"));
        } else {
            this.getFetchContentButton().disabled = true;
            this.fetchChapters();
        }
    }

    fetchContent() {
        return this.fetchChapters();
    }

    setUiToShowLoadingProgress(length) {
        main.getPackEpubButton().disabled = true;
        this.getProgressBar().max = length + 1;
        this.getProgressBar().value = 1;
    }

    fetchChapters() {
        let that = this;

        let pagesToFetch = that.chapters.filter(c => c.isIncludeable);
        if (pagesToFetch.length === 0) {
            return Promise.reject(new Error("No chapters found."));
        }

        this.setUiToShowLoadingProgress(pagesToFetch.length);

        var sequence = Promise.resolve();

        that.imageCollector.reset();
        that.imageCollector.setCoverImageUrl(CoverImageUI.getCoverImageUrl());

        let initialHostName = this.initialHostName();
        pagesToFetch.forEach(function(chapter) {
            
            sequence = sequence.then(function () {
                return that.fetchChapter(chapter.sourceUrl);
            }).then(function (chapterDom) {
                chapter.rawDom = chapterDom;
                let pageParser = that.parserForChapter(initialHostName, chapter);
                pageParser.removeUnusedElementsToReduceMemoryConsumption(chapterDom);
                pageParser.updateLoadState(chapter);
                let content = pageParser.findContent(chapter.rawDom);
                if (content == null) {
                    chapter.isIncludeable = false;
                    let errorMsg = chrome.i18n.getMessage("errorContentNotFound", [chapter.sourceUrl]);
                    throw new Error(errorMsg);
                }
                return pageParser.fetchImagesUsedInDocument(content);
            }); 
        });
        sequence = sequence.then(function() {
            that.getFetchContentButton().disabled = false;
            main.getPackEpubButton().disabled = false;
        }).catch(function (err) {
            ErrorLog.log(err);
        })
        return sequence;
    }

    initialHostName() {
        return util.extractHostName(this.chapterListUrl);
    }

    parserForChapter(initialNostName, chapter) {
        if (util.extractHostName(chapter.sourceUrl) === initialNostName) {
            return this;
        }
        let pageParser = parserFactory.fetch(chapter.sourceUrl, chapter.rawDom);
        if (pageParser === undefined) {
            return this;
        }
        pageParser.copyState(this);
        return pageParser;
    }

    fetchImagesUsedInDocument(content) {
        let that = this;
        return ImageCollector.replaceHyperlinksToImagesWithImages(content)
        .then(function (revisedContent) {
            that.imageCollector.findImagesUsedInDocument(revisedContent);
            return that.imageCollector.fetchImages(() => { });
        });
    }

    /**
    * default implementation
    * derivied classes can override if DOM has lots of elements not used in epub
    */
    removeUnusedElementsToReduceMemoryConsumption(chapterDom) {
        util.removeElements(chapterDom.querySelectorAll("select, iframe"));
    }

    // Hook if need to chase hyperlinks in page to get all chapter content
    fetchChapter(url) {
        return HttpClient.wrapFetch(url).then(function (xhr) {
            return Promise.resolve(xhr.responseXML);
        });
    }

    updateLoadState(chapter) {
        chapter.stateColumn.innerText = "Yes";
        this.getProgressBar().value += 1;
    }

    getProgressBar() {
        return document.getElementById("fetchProgress");
    }

    getFetchContentButton() {
        return document.getElementById("fetchChaptersButton")
    }

    // pack the raw chapter HTML into a zip file (for later manual analysis)
    packRawChapters() {
        let that = this;
        let zipFile = new JSZip();
        for (let i = 0; i < that.chapters.length; ++i) {
            if (that.chapters[i].rawDom != null) {
                zipFile.file("chapter" + i + ".html", that.chapters[i].rawDom.documentElement.outerHTML, { compression: "DEFLATE" });
            };
        }
        zipFile.generateAsync({ type: "blob" }).then(function(content) {
            EpubPacker.save(content, "raw.zip");
        }).catch(function(error) {
            ErrorLog.showErrorMessage(error);
        });
    }

    // Hook point, when need to do something when "Pack EPUB" pressed
    onStartCollecting() {
    }    
}
