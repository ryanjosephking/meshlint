" If you have cnee, and an /identical/ setup to mine, this will work as-is. I
" think it would require you to have Blender on Workspace 3, switchable if you
" hit Alt+F3, and stuff like that. Basically, you should probably re-record
" using the dev/record script, and then it will drastically help your
" workflow. With one button you can save the current file, switch to Blender,
" Alt+r,Enter to reload the code in the Text Editor, then Alt+p it and do
" whatever test you want (I kept the "whatever test" part pretty minimal, so
" it wouldn't get in the way when I wanted to do something else).
map <f5> :up<cr>:!./replay 2>&1 > /dev/null &<cr>

cd dev " <-- I don't like this. FIXME
