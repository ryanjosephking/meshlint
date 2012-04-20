test:
	cd dev; ./replay

README.mediawiki: README.md meshlint.py mkblenderwiki
	./mkblenderwiki README.md > $@
	xclip < $@
	firefox-bin "`./mkblenderwiki --wiki-edit-url`"
