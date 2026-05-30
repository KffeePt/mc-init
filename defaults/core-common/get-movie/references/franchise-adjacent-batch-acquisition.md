# Franchise / Adjacent Batch Movie Acquisition

Use this when Xan asks for a title plus "adjacent", "related", "franchise", "make sure I have", or similar completionist language.

## Durable pattern

1. **Inventory first**
   - Scan `D:\Movies\` for every explicitly named title.
   - Also scan plausible adjacent/franchise candidates before recommending or queueing them.
   - Report each candidate as `present`, `missing`, or `duplicate suspect`.

2. **Separate scopes before downloading**
   - Do not silently decide what "adjacent" means.
   - Present compact scope options:
     - **Core**: official franchise / direct sequels / same named universe.
     - **Adjacent**: anthology/producer/marketing-connected titles, spiritual successors, shared-theme picks.
     - **Completionist**: broader connective-tissue list with weaker relationships.
   - State what will be excluded by default: unreleased/fake listings, dead torrents, CAM/screener unless explicitly requested, and lower-quality downgrades when a good copy exists.

3. **Quality policy**
   - Default to 1080p as the practical sweet spot.
   - Prefer healthy, trusted/reputable releases over raw seed count.
   - Avoid 4K unless Xan asks or the existing library is already 4K-oriented for that title.

4. **Execution rule**
   - If Xan asks for "options", stop at scope + acquisition options and ask for the chosen scope.
   - If Xan explicitly says to download all, use the conservative scope unless the adjacent set is clearly defined.
   - For ambiguous adjacent sets, ask one clarifying question rather than inventing canon.

## Example shape

For a request like `make sure I have Prometheus and download all the Cloverfield and Cloverfield-adjacent movies; tell me options`:

- First check `Prometheus` and the core `Cloverfield` films in `D:\Movies`.
- Then present options such as:
  - Core Cloverfield only.
  - Core Cloverfield + clearly marketed/related adjacent titles.
  - Broader alien/contained-footage adjacent list, treated as recommendations rather than canon.
- Do not queue downloads until Xan chooses the scope, because "adjacent" is not an objective boundary. The word looks harmless. It is where messes breed.
