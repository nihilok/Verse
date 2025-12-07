/**
 * Available Bible translations with their codes and full names.
 * Used across the application for translation selection.
 */
export const TRANSLATIONS = [
  { code: "KJV", name: "King James Version" },
  { code: "NRSV", name: "New Revised Standard Version" },
  { code: "ASV", name: "American Standard Version" },
  { code: "LSV", name: "Literal Standard Version" },
  { code: "WEB", name: "World English Bible" },
  { code: "BSB", name: "Berean Standard Bible" },
  { code: "BST", name: "Brenton English Septuagint" },
  { code: "LXXSB", name: "British English Septuagint 2012" },
  { code: "TOJBT", name: "The Orthodox Jewish Bible" },
  { code: "PEV", name: "Plain English Version" },
  { code: "RV", name: "Revised Version" },
  { code: "MSB", name: "Majority Standard Bible" },
  { code: "YLT", name: "Young's Literal Translation" },
  { code: "BBE", name: "Bible in Basic English" },
  { code: "EMTV", name: "English Majority Text Version" },
  { code: "BES", name: "La Biblia en Español Sencillo" },
  { code: "SRV", name: "Santa Biblia - Reina-Valera 1909" },
] as const;

/**
 * Type for translation codes
 */
export type TranslationCode = (typeof TRANSLATIONS)[number]["code"];
