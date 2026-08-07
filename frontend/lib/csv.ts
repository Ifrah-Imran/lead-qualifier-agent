export type CsvLeadRow = {
  company_name: string;
  website_url: string;
  founder_name: string | null;
  founder_title: string | null;
  location: string | null;
  notes: string | null;
};

export type ParseCsvResult = {
  rows: CsvLeadRow[];
  errors: string[];
};

const REQUIRED_COLUMNS = ["company_name", "website_url"] as const;
const OPTIONAL_COLUMNS = ["founder_name", "founder_title", "location", "notes"] as const;

/** Split one CSV line into fields, honoring double-quoted fields with embedded commas. */
function splitLine(line: string): string[] {
  const fields: string[] = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];

    if (inQuotes) {
      if (char === '"') {
        if (line[i + 1] === '"') {
          current += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        current += char;
      }
      continue;
    }

    if (char === '"') {
      inQuotes = true;
    } else if (char === ",") {
      fields.push(current);
      current = "";
    } else {
      current += char;
    }
  }
  fields.push(current);
  return fields.map((f) => f.trim());
}

/** Parse a leads CSV. Requires company_name + website_url columns; the rest are optional. */
export function parseLeadsCsv(text: string): ParseCsvResult {
  const lines = text.split(/\r\n|\r|\n/).filter((line) => line.trim().length > 0);
  if (lines.length === 0) {
    return { rows: [], errors: ["The CSV file is empty."] };
  }

  const header = splitLine(lines[0]).map((h) => h.toLowerCase());
  const missing = REQUIRED_COLUMNS.filter((col) => !header.includes(col));
  if (missing.length > 0) {
    return {
      rows: [],
      errors: [
        `Missing required column${missing.length > 1 ? "s" : ""}: ${missing.join(", ")}. ` +
          `Required: ${REQUIRED_COLUMNS.join(", ")}. Optional: ${OPTIONAL_COLUMNS.join(", ")}.`,
      ],
    };
  }

  const rows: CsvLeadRow[] = [];
  const errors: string[] = [];

  for (let i = 1; i < lines.length; i++) {
    const fields = splitLine(lines[i]);
    const byCol = (col: string): string => {
      const idx = header.indexOf(col);
      return idx === -1 ? "" : (fields[idx] ?? "").trim();
    };

    const company_name = byCol("company_name");
    const website_url = byCol("website_url");
    if (!company_name || !website_url) {
      errors.push(`Row ${i + 1}: missing company_name or website_url — skipped.`);
      continue;
    }

    rows.push({
      company_name,
      website_url,
      founder_name: byCol("founder_name") || null,
      founder_title: byCol("founder_title") || null,
      location: byCol("location") || null,
      notes: byCol("notes") || null,
    });
  }

  return { rows, errors };
}
