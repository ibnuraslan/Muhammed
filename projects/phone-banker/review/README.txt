THE PHONE THAT KILLED A BANKER - render package
====================================================
6 parts (phone_banker_part01of06.zip ... phone_banker_part06of06.zip) + phone_banker_audio.zip

1. Put all 6 part zips and MERGE_PHONE_BANKER.bat in one folder.
2. Double-click MERGE_PHONE_BANKER.bat. It extracts every part into phone_banker_film\ and checks that all
   382 files arrived. (Without Windows: extract every zip into the same folder; they share the top folder.)
3. Upload or open phone_banker_film\out\blend\film\phone_banker_film.blend and render the animation
   (frames 1-9247, 1920x816, 24 fps, Cycles 32 samples, denoise). Keep the folder structure as it is: the film file
   links the shot files in out\blend\<part>\ and the textures in out\blend\textures\ by relative paths.
   Memory: opening the film file takes about 9.5 GB of RAM; rendering peaks at about 12 GB (16 GB machines are fine).

Audio (phone_banker_audio.zip): the full mix with voice and without voice, WAV 48 kHz and MP3 previews, exactly the
length of the film; lay either one under the rendered frames from frame 1.
