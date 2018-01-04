﻿using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using AngleSharp.Dom;
using AngleSharp.Dom.Html;
using AngleSharp.Extensions;
using WebNovelConverter.Sources.Models;
using System.Text.RegularExpressions;

namespace WebNovelConverter.Sources
{
    public class BakaTsukiSource : WebNovelSource
    {
        public override string BaseUrl => "https://www.baka-tsuki.org";

        public static readonly string[] PossibleChapterNameParts =
        {
            "illustrations",
            "preface",
            "glossary",
            "prologue",
            "introduction",
            "chapter",
            "afterword",
            "epilogue",
            "interlude"
        };

        private static readonly Regex WidthRegex = new Regex(@"width\=([0-9]+)", RegexOptions.Compiled);

        public BakaTsukiSource() : base("BakaTsuki")
        {
        }

        public override async Task<IEnumerable<ChapterLink>> GetChapterLinksAsync(string baseUrl, CancellationToken token = default(CancellationToken))
        {
            string baseContent = await GetWebPageAsync(baseUrl, token);

            IHtmlDocument doc = await Parser.ParseAsync(baseContent, token);

            IElement contentElement = doc.GetElementById("mw-content-text");

            if (contentElement == null)
                return null;

            var possibleChapters = from e in contentElement.Descendents<IElement>()
                                   where e.LocalName == "a"
                                   let parent = e.ParentElement
                                   where parent != null
                                   where parent.LocalName == "li"
                                   let secondParent = parent.ParentElement
                                   where secondParent != null
                                   where secondParent.LocalName == "ul"
                                   select e;

            return CollectChapterLinks(baseUrl, possibleChapters);
        }

        protected override IEnumerable<ChapterLink> CollectChapterLinks(string baseUrl, IEnumerable<IElement> linkElements, Func<IElement, bool> linkFilter = null)
        {
            foreach (IElement possibleChapter in linkElements)
            {
                if (!possibleChapter.HasAttribute("href"))
                    continue;

                string chTitle = WebUtility.HtmlDecode(possibleChapter.TextContent);
                string chLink = possibleChapter.GetAttribute("href");
                chLink = UrlHelper.ToAbsoluteUrl(BaseUrl, chLink);

                ChapterLink link = new ChapterLink
                {
                    Name = chTitle,
                    Url = chLink,
                    Unknown = true
                };

                if (PossibleChapterNameParts.Any(p => chTitle.IndexOf(p, StringComparison.CurrentCultureIgnoreCase) >= 0))
                    link.Unknown = false;

                yield return link;
            }
        }

        public override async Task<WebNovelInfo> GetNovelInfoAsync(string baseUrl, CancellationToken token = default(CancellationToken))
        {
            string baseContent = await GetWebPageAsync(baseUrl, token);

            IHtmlDocument doc = await Parser.ParseAsync(baseContent, token);

            var title = doc.QuerySelector("h1#firstHeading span")?.TextContent;

            string coverUrl = null;
            var coverUrlEl = doc.QuerySelector("div.thumb a.image img.thumbimage[src*=cover]");
            if( coverUrlEl != null)
            {
                coverUrl = coverUrlEl.Attributes["src"].Value;

                // Bigger thumbnail
                if(coverUrl.Contains("width=") && coverUrlEl.HasAttribute("data-file-width"))
                {
                    var width = Math.Min(int.Parse(coverUrlEl.Attributes["data-file-width"].Value)-1, 500);
                    coverUrl = WidthRegex.Replace(coverUrl, "width=" + width);
                }

                // Make URL absolute
                if( coverUrl.StartsWith("/"))
                {
                    coverUrl = new Uri(new Uri(baseUrl), coverUrl).AbsoluteUri;
                }
            }

            return new WebNovelInfo
            {
                Title = title,
                CoverUrl = coverUrl
            };
        }

        public override async Task<WebNovelChapter> GetChapterAsync(ChapterLink link,
            ChapterRetrievalOptions options = default(ChapterRetrievalOptions),
            CancellationToken token = default(CancellationToken))
        {
            string baseContent = await GetWebPageAsync(link.Url, token);

            IHtmlDocument doc = await Parser.ParseAsync(baseContent, token);
            IElement contentElement = doc.GetElementById("mw-content-text");

            if (contentElement == null)
                return null;

            doc.GetElementById("toc")?.Remove();

            RemoveTables(contentElement);

            foreach (IElement linkElement in contentElement.Descendents<IElement>().Where(p => p.LocalName == "a"))
            {
                if (!linkElement.HasAttribute("href"))
                    continue;

                string rel = WebUtility.HtmlDecode(linkElement.GetAttribute("href"));

                linkElement.SetAttribute("href", UrlHelper.ToAbsoluteUrl(BaseUrl, rel));

                IElement imgElement = linkElement.Descendents<IElement>().FirstOrDefault(p => p.LocalName == "img");

                if (imgElement != null)
                {
                    foreach (var attrib in imgElement.Attributes.Where(p => p.LocalName != "width" && p.LocalName != "height").ToList())
                        imgElement.RemoveAttribute(attrib.Name);

                    string linkImgUrl = linkElement.GetAttribute("href");
                    string imgPageContent = await GetWebPageAsync(linkImgUrl, token);

                    IHtmlDocument imgDoc = await Parser.ParseAsync(imgPageContent, token);

                    IElement fullImageElement = (from e in imgDoc.Descendents<IElement>()
                                                 where e.LocalName == "div"
                                                 where e.HasAttribute("class")
                                                 let classAttribute = e.GetAttribute("class")
                                                 where classAttribute == "fullMedia"
                                                 let imgLink = e.Descendents<IElement>().FirstOrDefault(p => p.LocalName == "a")
                                                 select imgLink).FirstOrDefault();

                    if (fullImageElement == null || !fullImageElement.HasAttribute("href"))
                        continue;

                    string imageLink = fullImageElement.GetAttribute("href");

                    imgElement.SetAttribute("src", UrlHelper.ToAbsoluteUrl(BaseUrl, imageLink));
                }
            }

            return new WebNovelChapter
            {
                Url = link.Url,
                Content = contentElement.InnerHtml
            };
        }

        protected virtual void RemoveTables(IElement element)
        {
            element.Descendents<IElement>().Where(p => p.LocalName == "table").ToList().ForEach(p => p.Remove());
        }
    }
}
