
Read my publications in the cs.bib file, which lists all of my publications in the computer science field. You can find the details of each publication, including the title, authors, and publication venue, in the cs.bib file.

Now I want to generate HTML files as well as a PDF file. The HTML files will provide a web-friendly format for viewing the publications, while the PDF files will offer a more traditional format for reading and sharing.

To generate HTML files from the cs.bib file, you can use a tool like BibTeX or a custom script that parses the .bib file and creates HTML output. For example, you can use Python with the BibTeX parser library to read the .bib file and generate HTML files for each publication.

To generate a PDF file from the cs.bib file, you can use a LaTeX template that includes the bibliography. You can compile the LaTeX document to produce a PDF that lists all of your publications in a well-formatted manner.

For HTML files, refer to https://research.google/teams/applied-science/ for examples of how to structure the HTML output.
I have also showed some screenshots of the generated HTML files in the "html_examples" folder for your reference (a1.png is the publication list page and if the mouse hovers on one article, a window pops up as shown in a2.png. And one click on the `detail` button in a2, it fires up a new page showing the particular article's details). Try your best to make the layout (but not the style) of the generated HTML files similar to those examples. For style and colors, please follow the RPG aesthetic as described in Rule 23, and avoid the "AI slop" aesthetic by making creative and distinctive design choices as outlined in Rule 24.


Rules to follow:

1. The page header should be in this format (`...` is the placeholder) 
```
div class="page-header">... <h1>Publications</h1>...<p>... publications by Chunhua Shen</p> ... </div>
```

2. `$...$` in the bibtex file should be rendered as LaTeX text, which can be rendered as SVG or PNG image.

3. The bibtex information in each article HTML file should include title, author, where it's published, year, note if available. The bibtex information should be properly formatted/aligned. Long lines (e.g. the `author` field) must wrap within the code block — use `white-space: pre-wrap` and `word-break: break-word` on the BibTeX block.

4. The generated HTML files should be self-contained (no external CSS or JS files) except for MathJax, which can be loaded from a CDN.

5. The generated HTML files should be static (no server-side code) and can be opened directly in a web browser.

6. The generated HTML files should be well-structured and semantically correct, using appropriate HTML tags for headings, paragraphs, lists, etc

7. The design should be clean and professional, with a focus on readability and usability. Besides the publication list page, each article's detail page should include a breadcrumb navigation (e.g., Home › Publications › Article Title) and action buttons for downloading the paper, viewing it on arXiv, visiting the project page, etc. The abstract should be displayed in a two-column layout with the label on the left and the text on the right. The BibTeX information should be displayed in a code block with proper formatting and alignment. Importantly, the article title should be rendered with MathJax to properly display any LaTeX math expressions included in the title.

8. The generated HTML files should be designed to be easily maintainable and updatable, allowing for new publications to be added to the cs.bib file and automatically reflected in the generated HTML output when the generation script is rerun.

9. The generated HTML files should be responsive and mobile-friendly, ensuring that they display well on various screen sizes and devices. This includes using flexible layouts, scalable images, and appropriate font sizes to enhance readability on smaller screens.

10. The generated HTML files should include a search functionality on the publication list page, allowing users to quickly find specific publications by title, author, or venue. This can be implemented using JavaScript to filter the displayed publications in real-time as the user types their search query. 

11. The generated HTML files should include a filtering mechanism on the publication list page, allowing users to filter publications by venue (e.g., CVPR, TPAMI, NeurIPS. Venues are listed as buttons. Only list CVPR, ICCV, ECCV, ICML, NeurIPS, ICLR, TPAMI, IJCV. and "show more", following the style/format in ./html_examples/a4.png) and by year. This can be implemented using JavaScript to show or hide publications based on the selected filters, providing an intuitive way for users to navigate through the publication list. Primary venue buttons (CVPR, ICCV, etc.) show a styled tooltip on hover indicating the paper count, e.g. "Show 102 CVPR papers authored by Chunhua Shen".

12. The generated HTML files should include a navigation mechanism on the publication list page that allows users to quickly jump to publications from specific years. This can be implemented as a sidebar or a dropdown menu that lists the years, enabling users to easily access publications from their desired time period.

13. The generated HTML files should include a preview feature on the publication list page, allowing users to hover over a publication entry to see a popup with the abstract text and a "View details" button. This can be implemented using JavaScript to display a tooltip or modal when the user hovers over a publication, providing a quick way to access the abstract without navigating away from the list page.

14. The generated HTML files should be designed with accessibility in mind, ensuring that they are usable by individuals with disabilities. This includes using semantic HTML elements, providing alternative text for images, ensuring sufficient color contrast, and making the site navigable via keyboard. Additionally, the design should be tested with screen readers to ensure that all content is accessible to users who rely on assistive technologies.

15. The generated HTML files should be optimized for performance, ensuring that they load quickly and efficiently. This can be achieved by minimizing the use of large images, optimizing CSS and JavaScript code, and leveraging browser caching. Additionally, the HTML files should be structured in a way that allows for efficient rendering by web browsers, such as using appropriate HTML tags and avoiding unnecessary nesting of elements.

16. The generated HTML files should include a consistent and visually appealing design, using a cohesive color scheme, typography, and layout. This can be achieved by defining a set of styles that are applied consistently across all pages, creating a unified look and feel for the publication list and detail pages. The design should also prioritize readability and usability, ensuring that users can easily navigate and consume the content on the site. In particular, please use the Claude code front-design skill which can be found bere: https://github.com/anthropics/claude-code/blob/main/plugins/frontend-design/skills/frontend-design/SKILL.md

17. The generated HTML files should include a mechanism for users to easily share publications on social media platforms. This can be implemented by adding social media sharing buttons (e.g., Twitter, Facebook, LinkedIn) to each publication entry on the list page and on the detail pages. When a user clicks on a sharing button, it should open a new window with a pre-populated message that includes the publication title and a link to the publication's detail page, making it easy for users to share their work with their network.

18. The generated HTML files should include a mechanism for users to provide feedback or report issues with the publication entries. This can be implemented by adding a "Report an issue" button on each publication entry and on the detail pages. When a user clicks on this button, it should open a form where they can submit their feedback or report any inaccuracies in the publication information. The form submissions can be sent to the github repo configured in `config.py` (`GITHUB_REPO_URL`). If `GITHUB_REPO_URL` is blank, the report-issue button is omitted entirely. Similarly, social share buttons require `SITE_BASE_URL` to be set in `config.py`.

19. For the preview pages, the abstract content will be (or is) stored in a separate file named `abstracts/<key>.txt`, where `<key>` corresponds to the BibTeX entry key. The `generate.py` script should read the abstract text from these files and include it in the preview popups on the publication list page, as well as on the individual article detail pages. This allows for a clean separation of the abstract content from the main BibTeX data, making it easier to manage and update abstracts without modifying the core publication data.  If an abstract file is missing for a publication, the script should handle this gracefully by displaying a message such as "Abstract not available" in the preview popup and on the detail page, ensuring that the user experience remains consistent even when some abstracts are not provided.

20. On the individual article detail pages, the action buttons (Download, arXiv, Project Page, Google Scholar) should be generated based on the presence of corresponding fields in the BibTeX entries. For example, if a BibTeX entry includes a `url` field that points to the project page, the "Project Page" button should be displayed and linked to that URL. Similarly, if there is an `arxiv/eprint` field with the arXiv identifier, the "arXiv" button should link to the appropriate arXiv page. The "Download" button can link to a PDF file if a `pdf` field is present in the BibTeX entry. If any of these fields are missing for a publication, the corresponding buttons should be omitted from the detail page to maintain a clean and relevant user interface.
The buttons should be styled consistently and placed prominently on the detail page to encourage users to access the additional resources related to each publication.

21. On the publication index page, if there is a `note` entry in the bibtex file, it should be displayed prominently next to the publication entry, styled in a way that distinguishes it from the main publication information (e.g., using a different color or font style). The `note` field can contain important information such as awards, special recognitions, or other relevant details about the publication that may be of interest to readers. By displaying this information clearly on the index page, users can quickly identify notable publications and gain additional context about the significance of each work.  The styling of the `note` field should be consistent across all publication entries to maintain a cohesive look and feel on the index page, while also ensuring that it stands out enough to catch the reader's attention without overwhelming the main publication details. Note that the `note` field should also be displayed on the individual article detail pages, providing users with comprehensive information about each publication in both the list and detail views. One more thing, I noticed that in the bibtex file's note entries, some of them concluded with . (e.g., "Best Paper Award."), while some of them did not (e.g., "Best Paper Award"). To maintain consistency in the display of the `note` field across all publications, the `generate.py` script should be designed to check for the presence of a period (or any other symbols) at the end of the `note` text. If a period/symbol is present, the script should automatically remove it to ensure that all notes are displayed in a uniform manner. This small detail can enhance the professionalism and readability of the publication list, providing a polished and cohesive presentation of the information. Notes are styled as an outlined italic badge (Cormorant Garamond, accent-red border and text, no uppercase) consistent with the editorial style.

22. On the publication index page, articles are grouped by year, with the most recent publications appearing at the top of the list. Publications in the same year should be grouped by venue, with the most prestigious venues (e.g., CVPR, TPAMI, NeurIPS, ICML, ICLR, IJCV, ICCV, ECCV, SIGRAPH) appearing first within each year group. This grouping and sorting mechanism allows users to easily navigate through the publication list and quickly identify the most recent and significant works in each year. The venue names should be displayed prominently as subheadings within each year group, providing clear visual cues for users to differentiate between different publication venues. Additionally, the sorting of publications within each venue group can be further refined by considering factors such as citation count or relevance, ensuring that the most impactful publications are highlighted for users browsing through the list.

23. Always design with Editorial Style
- Think Cosmopolitan, Vogue, and similar high-end publications. Inspired by traditional print magazines, this style transforms websites into immersive editorial experiences.

- Key elements:
a). Contrasting typography. Large decorative headlines paired with small, legible sans‑serif body text. Place headlines directly on images or in separate blocks.
b). Multilayer composition. Complex compositions reminiscent of magazine spreads. Take cues from top-tier publications like Esquire, GQ, or Harper's Bazaar.
c). Focus is on visual content. Images and videos are bold and eye-catching, designed to immediately draw the user's attention. Strong visuals are key, so be especially selective with your photography.
d). Decorative elements. Lines, frames, icons, and other graphics add visual interest and personality. Quotes or key phrases are often highlighted with large type or color to stand out. Use these accent and decorative elements to break up content and build a clear visual structure.
Please see ./html_examples/a6.jpg for an example of the editorial style.

24. You tend to converge toward generic, "on distribution" outputs. In frontend design,this creates what users call the "AI slop" aesthetic. Avoid this: make creative,distinctive frontends that surprise and delight. 

Focus on:
- Typography: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics.
- Color & Theme: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes. Draw from IDE themes and cultural aesthetics for inspiration.
- Motion: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions.
- Backgrounds: Create atmosphere and depth rather than defaulting to solid colors. Layer CSS gradients, use geometric patterns, or add contextual effects that match the overall aesthetic.

Avoid generic AI-generated aesthetics:
- Overused font families (Inter, Roboto, Arial, system fonts)
- Clichéd color schemes (particularly purple gradients on white backgrounds)
- Predictable layouts and component patterns
- Cookie-cutter design that lacks context-specific character

Interpret creatively and make unexpected choices that feel genuinely designed for the context. Vary between light and dark themes, different fonts, different aesthetics. You still tend to converge on common choices (Space Grotesk, for example) across generations. Avoid this: it is critical that you think outside the box!

25. Capitalize the first word of the title/heading and of any subtitle/subheading
Capitalize all major words (nouns, verbs including phrasal verbs such as "play with", adjectives, adverbs, and pronouns) in the title/heading (article's title, e.g.), including the second part of hyphenated major words (e.g., Self-Report not Self-report). Capitalize all words of four letters or more.
 
26. A light/dark theme toggle button is placed in the top-right corner of the header on every page (both index and detail pages). It shows a moon icon in light mode and a sun icon in dark mode. The chosen theme is persisted in `localStorage` and automatically respects the OS `prefers-color-scheme` setting on first visit. All colours are defined as CSS custom properties so the entire palette switches cleanly. Dark theme uses warm near-black backgrounds (`#141210`) rather than cold blue-blacks.

27. All site-specific configuration lives in `config.py`. The `generate.py` script must not contain any hardcoded author names, URLs, or repo paths. In particular:
- `AUTHOR_NAME` — the highlighted author (underlined in all author lists)
- `SITE_BASE_URL` — base URL used for social share links; leave `""` to disable share buttons
- `GITHUB_REPO_URL` — repo URL for the "Report issue" button; leave `""` to disable that button
- `PRIMARY_VENUES`, `VENUE_ORDER`, `BIB_FILE`, `ABSTRACT_DIR`, `DETAILS_DIR` — as before

Last but not least, generate and save all the needed Python code in the working directory such that next time when you want to update the publication list, you can simply update the `cs.bib` file and rerun the `generate.py` script to regenerate all the HTML files with the latest publication data. This ensures that the publication list remains up-to-date and accurate with minimal effort.

-- HTML generation (`generate.py`)

A Python script `generate.py` should be written to parse `cs.bib` and produce all HTML output.
Dependency: bibtexparser and run the script using the tool `uv`, instead of pip or conda, to avoid any potential dependency conflicts with your existing Python environment. 


**Run:**
```bash
cd /path/to/www2
python3 generate.py
```

**Output:**

| File/Folder | Description |
|---|---|
| `index.html` | Publication list page — all 493 papers |
| `details/<key>.html` | One detail page per publication |

### `index.html` — Publication list page

Styled after https://research.google/teams/applied-science/:

- **Page header** (per Rule 1): `<div class="page-header"><h1>Publications</h1><p>493 publications by Chunhua Shen</p></div>`
- Publications sorted newest-first, grouped by year
- Each entry shows: title (linked), authors separated by `·` (Chunhua Shen underlined), full venue + year
- **Preview button** on each row → dropdown popup with abstract text and a **View details** button (matching `html_examples/a2.jpg`)
- Search box (filters by title/author/venue in real time)
- Venue filter buttons (CVPR, TPAMI, NeurIPS, …) with hover tooltips showing paper count
- Year jump navigation
- Light/dark theme toggle in header

### `details/<key>.html` — Individual article pages

One file per BibTeX entry (matching `html_examples/a3.jpg`):

- Breadcrumb: Home › Publications ›
- Large article title — **`$...$` math rendered via MathJax** (CDN, per Rule 2), e.g. `$\pi^3$`, `R$^2$-Seg`
- Authors (Chunhua Shen underlined), venue/year line
- Action buttons: **Download**, **arXiv**, **Project Page**, **Google Scholar**, **Copy Bibtex**, **Share (X/LinkedIn)**, **Report Issue** (last two conditional on `config.py`)
- **Abstract** section (two-column layout: label left, text right)
- **BibTeX** section (per Rule 3) — includes `title`, `author`, `booktitle`/`journal`, `year`, `note` (if present), column-aligned, lines wrap with `pre-wrap`
- Light/dark theme toggle in header

### Typography & font consistency

All UI elements — author names, venue strings, note badges, Preview button, View Details button, venue filter buttons — use **Cormorant Garamond** (display serif, `var(--disp)`), consistent with the overall editorial style. Navigation / label elements use **Barlow Condensed** (`var(--ui)`).

### Design notes

- No external CSS framework — all styles are self-contained inline `<style>` blocks
- MathJax 3 loaded from jsDelivr CDN; configured for inline `$...$` math
- Chunhua Shen is highlighted (underlined) wherever it appears in author lists
- Venue filter buttons have CSS-only custom tooltips (animated fade+slide, `::after` pseudo-element, no JS)
- Preview popup z-index stacking fixed via `.popup-open` class escalation on parent `.pub-entry`
