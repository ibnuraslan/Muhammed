Git transport only. Rebuild each normal zip with:  cat NAME.zip.part* > NAME.zip  then  sha256sum -c SHA256SUMS
Deliver the rebuilt .zip files (normal, independent, each < 300 MB). Never deliver the .part files.
Note for the user: Extract all zips into ONE folder -> upload the folder -> render MASTER.blend, scene MASTER, frames 1-N
(P1: 1-3945, P2: 1-3551, P3: 1-4680).
