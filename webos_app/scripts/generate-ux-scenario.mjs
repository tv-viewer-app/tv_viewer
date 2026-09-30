import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import pptxgen from "pptxgenjs";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const appDir = path.resolve(scriptDir, "..");
const repoRoot = path.resolve(appDir, "..");
const listingDir = path.join(repoRoot, "store-listings", "lg-webos");
const screenshotDir = path.join(listingDir, "screenshots");
const outputPath = path.join(
  listingDir,
  "TV-Viewer-LG-webOS-UX-Scenario-v2.25.0.pptx",
);

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "TV Viewer";
pptx.company = "TV Viewer";
pptx.subject = "LG webOS UX scenario and certification test flow";
pptx.title = "TV Viewer for LG webOS - UX Scenario";
pptx.lang = "en-US";
pptx.theme = {
  headFontFace: "Arial",
  bodyFontFace: "Arial",
  lang: "en-US",
};
pptx.defineSlideMaster({
  title: "CONTENT",
  background: { color: "F7F9FC" },
  objects: [
    {
      rect: {
        x: 0,
        y: 0,
        w: 13.333,
        h: 0.13,
        fill: { color: "1676D2" },
        line: { color: "1676D2" },
      },
    },
    {
      text: {
        text: "TV Viewer | LG webOS certification",
        options: {
          x: 0.55,
          y: 7.12,
          w: 5.5,
          h: 0.18,
          fontFace: "Arial",
          fontSize: 8,
          color: "6B7280",
          margin: 0,
        },
      },
    },
    {
      text: {
        text: "v2.25.0",
        options: {
          x: 11.75,
          y: 7.12,
          w: 1,
          h: 0.18,
          fontFace: "Arial",
          fontSize: 8,
          color: "6B7280",
          align: "right",
          margin: 0,
        },
      },
    },
  ],
  slideNumber: {
    x: 12.8,
    y: 7.12,
    w: 0.2,
    h: 0.18,
    fontFace: "Arial",
    fontSize: 8,
    color: "6B7280",
    align: "right",
    margin: 0,
  },
});

const COLORS = {
  blue: "1676D2",
  darkBlue: "0A2342",
  text: "172033",
  muted: "5F6B7A",
  border: "D7DFEA",
  paleBlue: "EAF3FC",
  green: "107C10",
  amber: "A15C00",
  white: "FFFFFF",
};

function addTitle(slide, title, subtitle) {
  slide.addText(title, {
    x: 0.58,
    y: 0.36,
    w: 8.8,
    h: 0.42,
    fontFace: "Arial",
    fontSize: 24,
    bold: true,
    color: COLORS.text,
    margin: 0,
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.6,
      y: 0.82,
      w: 11.8,
      h: 0.27,
      fontFace: "Arial",
      fontSize: 11,
      color: COLORS.muted,
      margin: 0,
    });
  }
}

function addScreenshot(slide, filename, x = 0.58, y = 1.28, w = 8.35) {
  const imagePath = path.join(screenshotDir, filename);
  if (!fs.existsSync(imagePath)) {
    throw new Error(`Missing screenshot: ${imagePath}`);
  }
  const h = w * (9 / 16);
  slide.addShape(pptx.ShapeType.rect, {
    x: x - 0.03,
    y: y - 0.03,
    w: w + 0.06,
    h: h + 0.06,
    fill: { color: "FFFFFF" },
    line: { color: COLORS.border, width: 1 },
    shadow: {
      type: "outer",
      color: "A7B2C0",
      blur: 2,
      angle: 45,
      distance: 1,
      opacity: 0.2,
    },
  });
  slide.addImage({ path: imagePath, x, y, w, h });
}

function addStepPanel(slide, title, steps, x = 9.2, y = 1.28, w = 3.55) {
  const h = 5.35;
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.06,
    fill: { color: "FFFFFF" },
    line: { color: COLORS.border, width: 1 },
  });
  slide.addText(title, {
    x: x + 0.24,
    y: y + 0.24,
    w: w - 0.48,
    h: 0.3,
    fontFace: "Arial",
    fontSize: 16,
    bold: true,
    color: COLORS.darkBlue,
    margin: 0,
  });
  let cursor = y + 0.72;
  steps.forEach((step, index) => {
    slide.addShape(pptx.ShapeType.ellipse, {
      x: x + 0.23,
      y: cursor,
      w: 0.31,
      h: 0.31,
      fill: { color: COLORS.paleBlue },
      line: { color: COLORS.blue, width: 1 },
    });
    slide.addText(String(index + 1), {
      x: x + 0.23,
      y: cursor + 0.03,
      w: 0.31,
      h: 0.18,
      fontFace: "Arial",
      fontSize: 9,
      bold: true,
      color: COLORS.blue,
      align: "center",
      margin: 0,
    });
    slide.addText(step, {
      x: x + 0.67,
      y: cursor - 0.01,
      w: w - 0.95,
      h: 0.56,
      fontFace: "Arial",
      fontSize: 10.5,
      color: COLORS.text,
      breakLine: false,
      valign: "top",
      margin: 0,
      fit: "shrink",
    });
    cursor += 0.82;
  });
}

function addExpected(slide, text, x = 0.58, y = 6.2, w = 8.35) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h: 0.56,
    rectRadius: 0.04,
    fill: { color: "EDF7ED" },
    line: { color: "9CCC9C", width: 1 },
  });
  slide.addText([
    { text: "Expected: ", options: { bold: true, color: COLORS.green } },
    { text, options: { color: COLORS.text } },
  ], {
    x: x + 0.18,
    y: y + 0.14,
    w: w - 0.36,
    h: 0.25,
    fontFace: "Arial",
    fontSize: 10,
    margin: 0,
    fit: "shrink",
  });
}

function addStatusBadge(slide, text, color, x, y, w) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h: 0.37,
    rectRadius: 0.05,
    fill: { color },
    line: { color },
  });
  slide.addText(text, {
    x,
    y: y + 0.075,
    w,
    h: 0.19,
    fontFace: "Arial",
    fontSize: 9,
    bold: true,
    color: COLORS.white,
    align: "center",
    margin: 0,
  });
}

{
  const slide = pptx.addSlide();
  slide.background = { color: "0B1320" };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 13.333,
    h: 7.5,
    fill: { color: "0B1320" },
    line: { color: "0B1320" },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: 8.55,
    y: 0,
    w: 4.783,
    h: 7.5,
    fill: { color: "12355B", transparency: 10 },
    line: { color: "12355B", transparency: 100 },
  });
  slide.addImage({
    path: path.join(appDir, "largeIcon.png"),
    x: 0.72,
    y: 0.72,
    w: 0.72,
    h: 0.72,
  });
  slide.addText("TV Viewer", {
    x: 1.63,
    y: 0.82,
    w: 3.2,
    h: 0.36,
    fontFace: "Arial",
    fontSize: 21,
    bold: true,
    color: COLORS.white,
    margin: 0,
  });
  slide.addText("LG webOS UX Scenario", {
    x: 0.72,
    y: 2.0,
    w: 7.35,
    h: 0.62,
    fontFace: "Arial",
    fontSize: 34,
    bold: true,
    color: COLORS.white,
    margin: 0,
  });
  slide.addText("Certification test flow and expected behavior", {
    x: 0.75,
    y: 2.77,
    w: 6.8,
    h: 0.34,
    fontFace: "Arial",
    fontSize: 18,
    color: "BDD5EE",
    margin: 0,
  });
  slide.addText("Package ID", {
    x: 0.75,
    y: 4.24,
    w: 1.4,
    h: 0.22,
    fontFace: "Arial",
    fontSize: 10,
    bold: true,
    color: "8FB8E8",
    margin: 0,
  });
  slide.addText("app.tvviewer.webos", {
    x: 0.75,
    y: 4.52,
    w: 3.5,
    h: 0.27,
    fontFace: "Arial",
    fontSize: 15,
    color: COLORS.white,
    margin: 0,
  });
  slide.addText("Version", {
    x: 4.52,
    y: 4.24,
    w: 1.1,
    h: 0.22,
    fontFace: "Arial",
    fontSize: 10,
    bold: true,
    color: "8FB8E8",
    margin: 0,
  });
  slide.addText("2.25.0", {
    x: 4.52,
    y: 4.52,
    w: 1.4,
    h: 0.27,
    fontFace: "Arial",
    fontSize: 15,
    color: COLORS.white,
    margin: 0,
  });
  slide.addText("Target", {
    x: 6.35,
    y: 4.24,
    w: 1.1,
    h: 0.22,
    fontFace: "Arial",
    fontSize: 10,
    bold: true,
    color: "8FB8E8",
    margin: 0,
  });
  slide.addText("LG webOS TV", {
    x: 6.35,
    y: 4.52,
    w: 1.8,
    h: 0.27,
    fontFace: "Arial",
    fontSize: 15,
    color: COLORS.white,
    margin: 0,
  });
  addStatusBadge(slide, "NO LOGIN", "1676D2", 9.18, 1.45, 2.65);
  addStatusBadge(slide, "REMOTE-FIRST", "1676D2", 9.18, 2.08, 2.65);
  addStatusBadge(slide, "NO ANALYTICS", "107C10", 9.18, 2.71, 2.65);
  addStatusBadge(slide, "PUBLIC-INTEREST CATALOG", "744DA9", 9.18, 3.34, 2.65);
  slide.addText("Prepared September 30, 2026", {
    x: 0.75,
    y: 6.68,
    w: 3.6,
    h: 0.24,
    fontFace: "Arial",
    fontSize: 10,
    color: "9FB4CA",
    margin: 0,
  });
}

{
  const slide = pptx.addSlide("CONTENT");
  addTitle(
    slide,
    "1. First launch and disclosure",
    "No catalog or stream request is made until the viewer accepts the first-run content and privacy notice.",
  );
  addScreenshot(slide, "00-first-run-notice.png");
  addStepPanel(slide, "Test procedure", [
    "Launch TV Viewer from the LG Apps launcher.",
    "Read the content-source and privacy notice.",
    "Choose Continue to accept the notice and load the catalog.",
  ]);
  addExpected(
    slide,
    "The notice is readable at TV distance, the background remains in a Waiting state, and no account sign-in is requested.",
  );
}

{
  const slide = pptx.addSlide("CONTENT");
  addTitle(
    slide,
    "2. Browse, search, and filter",
    "Discovery is limited to curated public-interest categories for the LG Content Store build.",
  );
  addScreenshot(slide, "01-catalog.png");
  addStepPanel(slide, "Test procedure", [
    "Use the D-pad to move through Search, Category, Type, and action buttons.",
    "Select Legislative or another public-interest category.",
    "Choose Find channels and move focus through the result grid.",
    "Press OK on a channel card to open playback.",
  ]);
  addExpected(
    slide,
    "Focused elements have a high-contrast white outline; category and result counts update; unavailable images do not block navigation.",
  );
}

{
  const slide = pptx.addSlide("CONTENT");
  addTitle(
    slide,
    "3. Playback and channel controls",
    "Playback uses the TV browser's native HLS support first, with a bundled HLS.js fallback.",
  );
  addScreenshot(slide, "03-player-controls.png");
  addStepPanel(slide, "Test procedure", [
    "Start a channel from the catalog.",
    "Use OK or the media Play/Pause key to control playback.",
    "Test Mute, Add favorite, and Next source when available.",
    "Select Back to channels or press the remote Back key.",
  ]);
  addExpected(
    slide,
    "Playback stays full-screen, controls remain remote reachable, failed sources show an error rather than freezing, and Back returns to the catalog.",
  );
}

{
  const slide = pptx.addSlide("CONTENT");
  addTitle(
    slide,
    "4. Remote-control and Magic Remote behavior",
    "All core functions are available without pointer input; Magic Remote pointer interaction remains supported.",
  );
  addScreenshot(slide, "02-remote-help.png");
  addStepPanel(slide, "Key mapping", [
    "Arrows: move focus spatially between controls.",
    "OK / Enter: activate the focused control.",
    "Back: close a dialog, leave playback, then exit from the catalog.",
    "Play/Pause and Stop: control active media.",
    "Pointer: hover and click the same focusable controls.",
  ]);
  addExpected(
    slide,
    "Focus never becomes trapped, the Help dialog can be closed by Back, and repeated Back follows a predictable dialog > player > app hierarchy.",
  );
}

{
  const slide = pptx.addSlide("CONTENT");
  addTitle(
    slide,
    "5. Data, network, and storage boundaries",
    "The webOS build is intentionally lightweight: no sign-in, no analytics SDK, no background service, and no Luna permissions.",
  );
  const cards = [
    {
      x: 0.62,
      title: "Catalog",
      body: "Read-only HTTPS request to the public, RLS-protected Supabase channel catalog after first-run acceptance.",
      color: "1676D2",
    },
    {
      x: 4.39,
      title: "Playback",
      body: "The TV connects directly to the selected broadcaster or community stream URL. TV Viewer does not relay or host video.",
      color: "744DA9",
    },
    {
      x: 8.16,
      title: "Local state",
      body: "Favorites and the accepted-notice flag are stored only in browser localStorage on the television.",
      color: "107C10",
    },
  ];
  cards.forEach((card) => {
    slide.addShape(pptx.ShapeType.roundRect, {
      x: card.x,
      y: 1.42,
      w: 3.55,
      h: 2.12,
      rectRadius: 0.06,
      fill: { color: "FFFFFF" },
      line: { color: COLORS.border, width: 1 },
    });
    slide.addShape(pptx.ShapeType.rect, {
      x: card.x,
      y: 1.42,
      w: 3.55,
      h: 0.11,
      fill: { color: card.color },
      line: { color: card.color },
    });
    slide.addText(card.title, {
      x: card.x + 0.24,
      y: 1.78,
      w: 2.9,
      h: 0.3,
      fontFace: "Arial",
      fontSize: 17,
      bold: true,
      color: COLORS.text,
      margin: 0,
    });
    slide.addText(card.body, {
      x: card.x + 0.24,
      y: 2.24,
      w: 3.02,
      h: 0.95,
      fontFace: "Arial",
      fontSize: 11,
      color: COLORS.muted,
      valign: "top",
      margin: 0,
      fit: "shrink",
    });
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.62,
    y: 4.05,
    w: 11.09,
    h: 1.8,
    rectRadius: 0.06,
    fill: { color: "FFF7E8" },
    line: { color: "E5B86B", width: 1 },
  });
  slide.addText("Certification notes", {
    x: 0.92,
    y: 4.37,
    w: 2.7,
    h: 0.3,
    fontFace: "Arial",
    fontSize: 17,
    bold: true,
    color: COLORS.amber,
    margin: 0,
  });
  slide.addText(
    "• Network access is required for both catalog loading and playback.\n" +
      "• Channel availability and geographic restrictions are controlled by third-party endpoints.\n" +
      "• The submitted package declares requiredACG: [] and requests no privileged webOS service access.\n" +
      "• Content-rights review remains a Seller Lounge approval dependency.",
    {
      x: 3.15,
      y: 4.28,
      w: 8.15,
      h: 1.15,
      fontFace: "Arial",
      fontSize: 11,
      color: COLORS.text,
      breakLine: false,
      valign: "mid",
      margin: 0,
      fit: "shrink",
    },
  );
}

{
  const slide = pptx.addSlide("CONTENT");
  addTitle(
    slide,
    "6. Certification execution and exit criteria",
    "Desktop automation supports preparation; final attestation requires an LG TV, App CTS, or Cloud Test Lab evidence.",
  );
  const rows = [
    ["Launch", "Cold and warm launch, splash, first-run notice", "Pending LG TV / Cloud Test Lab"],
    ["Input", "D-pad, OK, Back, media keys, Magic Remote pointer", "Pending LG TV / Cloud Test Lab"],
    ["Playback", "HLS start, pause, mute, source fallback, error recovery", "Pending LG TV / Cloud Test Lab"],
    ["Lifecycle", "Suspend/resume, relaunch, memory pressure behavior", "Pending LG TV / Cloud Test Lab"],
    ["Visual", "FHD and HD scaling, overscan, focus visibility, text legibility", "Pending LG TV / Cloud Test Lab"],
    ["Policy", "Territories, age rating, catalog/content-rights acceptance", "Pending Seller Lounge"],
  ];
  const tableX = 0.62;
  const tableY = 1.38;
  const colWidths = [1.55, 6.55, 3.98];
  const rowHeight = 0.54;
  const headers = ["Area", "Required evidence", "Current status"];
  let x = tableX;
  headers.forEach((header, index) => {
    slide.addShape(pptx.ShapeType.rect, {
      x,
      y: tableY,
      w: colWidths[index],
      h: rowHeight,
      fill: { color: COLORS.darkBlue },
      line: { color: COLORS.border, width: 1 },
    });
    slide.addText(header, {
      x: x + 0.12,
      y: tableY + 0.16,
      w: colWidths[index] - 0.24,
      h: 0.21,
      fontFace: "Arial",
      fontSize: 10.5,
      bold: true,
      color: COLORS.white,
      margin: 0,
    });
    x += colWidths[index];
  });
  rows.forEach((row, rowIndex) => {
    const y = tableY + rowHeight * (rowIndex + 1);
    x = tableX;
    row.forEach((cell, columnIndex) => {
      slide.addShape(pptx.ShapeType.rect, {
        x,
        y,
        w: colWidths[columnIndex],
        h: rowHeight,
        fill: { color: rowIndex % 2 === 0 ? "FFFFFF" : "F1F5FA" },
        line: { color: COLORS.border, width: 1 },
      });
      slide.addText(cell, {
        x: x + 0.12,
        y: y + 0.15,
        w: colWidths[columnIndex] - 0.24,
        h: 0.22,
        fontFace: "Arial",
        fontSize: 10,
        bold: columnIndex === 0,
        color: columnIndex === 2 ? COLORS.amber : COLORS.text,
        margin: 0,
        fit: "shrink",
      });
      x += colWidths[columnIndex];
    });
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.62,
    y: 5.55,
    w: 12.08,
    h: 0.9,
    rectRadius: 0.05,
    fill: { color: "EAF3FC" },
    line: { color: "9AC5EF", width: 1 },
  });
  slide.addText([
    {
      text: "Exit criteria: ",
      options: { bold: true, color: COLORS.blue },
    },
    {
      text:
        "every official checklist result is Pass or N/A with evidence; both installable webOS packages (IPKs) pass validation; LG App CTS and device-test results are attached; and Seller Lounge accepts the catalog model and territories.",
      options: { color: COLORS.text },
    },
  ], {
    x: 0.88,
    y: 5.83,
    w: 11.5,
    h: 0.34,
    fontFace: "Arial",
    fontSize: 11.5,
    margin: 0,
    fit: "shrink",
  });
}

await pptx.writeFile({ fileName: outputPath });
console.log(outputPath);
