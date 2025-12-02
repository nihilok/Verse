# Available English Translations Reference

This document lists English Bible translations available through the Hello.AO API that can be added to the Verse app.

## Currently Supported in Verse

| Code | Name | API ID | Notes |
|------|------|--------|-------|
| KJV | King James Version | eng_kjv | Classic 1611 translation |
| ASV | American Standard Version | eng_asv | 1901 revision of the RV |
| LSV | Literal Standard Version | eng_lsv | Modern literal translation |
| WEB | World English Bible | ENGWEBP | Modern public domain translation |
| BSB | Berean Standard Bible | BSB | Modern study Bible |

## Additional English Translations Available to Add

These translations are available in the Hello.AO API and can be added to Verse:

### Popular Historical Translations
- **DBY** - Darby Translation (`eng_dby`) - John Nelson Darby's translation
- **YLT** - Young's Literal Translation (`eng_ylt`) - Very literal translation
- **GNV** - Geneva Bible 1599 (`eng_gnv`) - Pre-KJV Protestant translation
- **DRA** - Douay-Rheims 1899 (`eng_dra`) - Catholic translation
- **BBE** - Bible in Basic English (`eng_bbe`) - Simple English vocabulary

### Modern Translations
- **FBV** - Free Bible Version (`eng_fbv`) - Contemporary language
- **NET** - NET Bible (`eng_net`) - With extensive study notes
- **MSB** - Majority Standard Bible (`eng_msb`) - Based on majority text
- **T4T** - Translation for Translators (`eng_t4t`) - Meaning-based translation
- **ULB** - Unlocked Literal Bible (`eng_ulb`) - Open license literal translation

### Specialized Translations
- **EMTV** - English Majority Text Version (`eng_emtv`) - Byzantine/Majority text basis
- **ASVBT** - ASV Byzantine Text (`eng_abt`) - ASV with Byzantine text base
- **TNTC** - Family 35 NT (`eng_f35`) - Based on Family 35 manuscripts
- **TCENT** - Text-Critical English NT (`eng_tce`) - Critical text NT only

### Septuagint & OT Translations
- **LXXSA** - LXX2012 U.S. English (`eng_lxx`) - Septuagint translation
- **LXXSB** - British English Septuagint 2012 (`eng_lxu`) - British English LXX
- **BST** - Brenton English Septuagint (`eng_bre`) - Classic LXX translation
- **UBES** - Updated Brenton English Septuagint (`eng_boy`) - Updated Brenton
- **JPSTN** - JPS TaNaKH 1917 (`eng_jps`) - Jewish Publication Society
- **ILT** - Leeser Tanakh (`eng_lee`) - Isaac Leeser's translation

### Other Notable Translations
- **WEBC** - World English Bible (Catholic) (`eng_webc`) - WEB with Deuterocanon
- **WEBBE** - World English Bible British Edition (`eng_webpb`) - British spelling
- **WMB** - World Messianic Bible (`eng_wmb`) - Messianic perspective
- **TNT** - Tyndale NT (`eng_tnt`) - William Tyndale's translation
- **GNB** - Noyes Bible (`eng_noy`) - George Noyes translation
- **GLW** - God's Living Word (`eng_glw`)

## Not Available (Copyrighted)

These popular translations are **NOT available** through Hello.AO API due to copyright restrictions:

- ❌ **NIV** - New International Version (requires Biblica license)
- ❌ **NRSV** - New Revised Standard Version (requires NCC license)
- ❌ **ESV** - English Standard Version (requires Crossway license)
- ❌ **NLT** - New Living Translation (requires Tyndale House license)
- ❌ **NASB** - New American Standard Bible (requires Lockman Foundation license)
- ❌ **CSB/HCSB** - Christian Standard Bible (requires Holman license)
- ❌ **NKJV** - New King James Version (requires Thomas Nelson license)
- ❌ **MSG** - The Message (requires NavPress license)

## How to Add a New Translation

### Backend (`backend/app/clients/helloao_client.py`)

Add to the `TRANSLATION_IDS` dictionary:
```python
TRANSLATION_IDS = {
    # ...existing entries...
    "CODE": "api_id",  # Description
}
```

### Frontend (`frontend/src/components/PassageSearch.tsx`)

Add to the `TRANSLATIONS` array:
```typescript
const TRANSLATIONS = [
  // ...existing entries...
  { code: "CODE", name: "Full Translation Name" },
];
```

## Translation Quality Notes

- **Literal**: KJV, ASV, LSV, YLT, DBY, EMTV, ULB
- **Balanced**: WEB, BSB, NET, FBV, MSB
- **Simple English**: BBE, T4T
- **Historical Interest**: GNV, DRA, TNT
- **Specialized**: LXX translations, JPSTN (OT only)

## Additional Resources

- Full list of translations: See `docs/available_translations.json`
- Hello.AO API documentation: https://scripture.api.bible
- API base URL: https://hello.ao
