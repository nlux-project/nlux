I want to enrich selected NLUX records with AI-enriched extra (meta-)data.
The goal is to provide extra data and/or corrections that can be applied 
by a human to a given record in their museum collection management system.

- Use ai-enrichment/ai-enrichment.py as a starting point, but feel free to
  augment or expand at your discretion
- The script will use a simple input file with a list of  NLUX Object ID's
  with done checkmarks as in:
  [ ] u09j0fn203iu4023fj2f <- not done
  [X] o-kc3-k4f-9328904230 <- done
- The script should use our own API endpoint at localhost:8000 to retrieve
  known data
- Use http://localhost:8000/data/object/05477c72-b195-413c-afc6-1473fd31d317 as
  the first record for development and testing
- Use prompt.md as a starting prompt for use in ai-enrichment.py but feel 
  free to change or expand. This prompt contains details on how/what to retrieve
- The script retrieves all details, including IIIF image and collects data from 
  Internet, and compares the retrieved details with the retrieved known data from our API. 
- results should be stored in a file with a link to the record
- results should be loaded in our API 
- results should be displayed in extra box in object details page in front-end
- So, the front-end should display an object, then do a check if there is AI-enriched
  metadata available for this record, if yes, display this also in a separate box. 
