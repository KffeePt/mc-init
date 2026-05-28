# Selection Followthrough — Media Downloads

## Trigger
Xan has already been shown media search results and then replies with a short confirmation such as:
- "ok that is it then pls add it"
- "grab option 1"
- "that one"
- "add it"

## Durable lesson
Treat the reply as an instruction to act on the previously recommended or explicitly numbered result. Preserve the option mapping from the prior assistant turn. Do not reinterpret the request as a new administrative/configuration task.

## Correct behavior
1. Identify the selected option from the previous results/recommendation.
2. Use the get-show qBittorrent workflow immediately.
3. Add the selected magnet to `D:\Shows\<Show Name>\`.
4. Verify via qBittorrent active torrent list that it was actually added and targeting the expected save path.
5. Report concise result: title, size, destination, verification status, and any warning.

## Pitfall
A generic "add it" is not ambiguous if the previous turn recommended one best bundle. Asking again or doing unrelated state/memory/artifact work is wrong. Context loss here is operationally expensive: it can leave Xan thinking the download was queued when it was not.
