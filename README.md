![MeshLint Logo](raw/master/img/logo-suzanne.png "The default Monkey has 32 Tris, 42 Nonmanifold Elements, and 9 6+-Edge Poles.")

A Blender Addon to help you keep your meshes clean and lint-free, like a
spell-checker for your meshes.

![Results with Suzanne](raw/master/img/messed-up-mesh.png "Found some Issues.")

Can check for:

 - Tris: Evil.
 - Ngons: Also pretty bad.
 - Nonmanifold Elements: Stray Verts and Edges that have < or > than 2 faces.
 - Interior Faces: Faces spanning inside the mesh that cause confusing
     effects with Subsurf and Edge Loops. By the Blender definition, this is
     only true for a face if absolutely none of its edges are connected to <=
     2 faces.
 - 6+-Poles: Verts with 6 or more edges (check disabled by default, because
   some meshes legitimately have these).
 - Default Names (like `Cube.002`)
 - Unapplied Scale (remember that `Ctrl+a,s` This causes so many problems I
   don't even plan on making it an optional warning. If you have a selection
   that includes an object with an Unapplied Scale, you'll hear about it from
   MeshLint)
 - ...can you think of more? We'll add them!

So if you click `Select Lint`, in Object or Edit Modes, it will set your
current selection to all elements that fail the enabled checks. A good thing
to do if you are having trouble finding pieces is to hit `Numpad '.'`, which
will center the 3D Viewport on the problems. You might have to do this
iteratively with `b`order selects and `Middle Mouse Button` to deselect the
elements you already know about.

![Live Update Screenshot](raw/master/img/infobar.png "Live update screnshot.")

Also, you can enable `Continuous Check`, which is a huge aspect to this. It is
good for cases where you think you won't be creating any new problem geometry.
Whenever something goes wrong, the Info Bar at the top will display a message
describing what MeshLint found. Also, you will notice the counts are updated.

Furthermore, it works on the whole selection (but starting with the Active
Object). So you can quickly check your entire scene with `a` to Select All and
then click `Select Lint`. The checker will stop on the first found bit of
lint, and throw you into Edit Mode so you can see it.

Getting
-------

Best way is to:

    git clone git@github.com:ryanjosephking/meshlint.git

That way, you can `git pull` later on and it will automatically refresh to the
latest (theoretically-)good version.

But I realize that not everyone has `git` or an operating system capable of
symlinking.

So, for those that can't: You can simply download the
[meshlint.py](https://raw.github.com/ryanjosephking/meshlint/master/meshlint.py)
script directly. (And re-visit that URL for the newest version, later on.)

Installing
----------

The super-awesome way is to directly symlink `meshlint.py` into your [Blender
Addons
Dir](http://wiki.blender.org/index.php/Doc:2.6/Manual/Introduction/Installing_Blender/DirectoryLayout).
The advantage is that the previous section's `git pull` will download the
newest version automatically. But not everyone can be expected to be
superawesome all the time, so continue on:

![Installing Addon](raw/master/img/install-addon.png "`Install Addon...` screen.")

Hit `Ctrl+Alt+u` to load up the User Preferences (I always use the keystroke
for this because of the occasional time where you miss, using the `File` menu,
and click `Save User Settings`. Click the `Install Addon...` button at the
bottom, then navigate to your `meshlint.py` script.

![The Enable Checkbox](raw/master/img/enable-checkbox.png "The Enable checkbox.")

Next, and this is a tricky bit, if you're not used to installing Addons: you
have to follow up by checking this little box on the right of the Addon entry
in the list. If, for some reason, you have a hard time finding it, you can
search for `MeshLint` or click on the `Mesh` button on the left. Hopefully,
though, it comes right up when you do `Install Addon...`.

If you want to keep MeshLint available (and who wouldn't?), follow the above
steps on a fresh `.blend` (one you `Ctrl+n`d), then hit `Ctrl+u` at this
point. The next time you run Blender you won't have to repeat the above.

![Where is it? -> In the Object Data properties](raw/master/img/where-is-it.png
"Object Data properties")

When installed, it will add a new Subpanel to the bottom of the `Object Data`
properties (the button in the `Properties Editor` that looks like the inverted
triangle).

Going Further
-------------

We really want to make this a top-grade Addon. This will take a bit of
debugging and brainstorming, both. There's a spot right below this text for a
"Thanks", for Blenderers who give such feedback.

<rking@panoptic.com>

Thanks
-----

- taniwha / Bill Currie - For being part of the original idea and for Alpha
  and Beta testing.
- endikos / William Knechtel - For also being an idea guy and tester, and for
  being a great Brother in the Lord, anyway.
- lsmft / Kevin Wood - For being a premeir Beta tester, complete with a [UI
  improvement mockup](raw/master/img/lsmft.png "Likes Sending Me Fine
  Templates"), and also for providing the hardware that was used to write it.
  (!)
- moth3r / Ivan Šantić - For being one of the most enthusiastic Blenderers I
  ever met, and for testing/feedback, too.
