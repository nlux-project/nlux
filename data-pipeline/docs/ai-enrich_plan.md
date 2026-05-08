# Plan: Enrich collection data with metadata separately harvested by AI

Please give me feedback and make a detailed implementation plan:

- A given collection (for example the NHA collections) that has gone through the data-pipeline
  will be given as input to a Python script which, record by record, does an extended search
  of the internet of the record object (or person/set/place) and compare the collected fields
  with metadata from the Internet, such as mistakes, additions, literature, etc.
- Prompt (generic) will have to be written separately
- The extended AI search analysis data will be added to a separate output file (preferred)
- As the last step in the data-pipeline the separate output file will be merged in export file
  but without changing the existing field values
- The AI metadata analysis data will be presented in the frontend in a separate 'box/card' so as to visually
  separate it from the regular harvested data (for the time being).

Example of AI search analysis data from a teylers museum object from a previous project (https://github.com/jsoeterbroek/teylers_collection_research): teylers-1355-analysis.md. Use this a guide of the amount/type of metadata I would like to see in the results.
