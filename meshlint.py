import bpy
import bmesh
import re

SUBPANEL_LABEL = 'Mesh Lint'

LINTS = [
  {
    'symbol': 'tris',
    'label': 'Tris',
    'default': True
  },
  {
    'symbol': 'ngons',
    'label': 'Ngons',
    'default': True
  },
  {
    'symbol': 'interior_faces',
    'label': 'Interior Faces',
    'default': True
  },
  {
    'symbol': 'nonmanifold',
    'label': 'Nonmanifold Elements',
    'default': True
  },
  {
    'symbol': 'sixplus_poles',
    'label': '6+-edge Poles',
    'default': False
  },
  # 'unnamed_object'
  # [Your great new idea here] -> Tell me about it: rking@panoptic.com
]

LINTS_LIST = ' / '.join(lint['label'] for lint in LINTS)

N_A_STR = '(N/A)'
TBD_STR = '...'

for lint in LINTS:
    sym = lint['symbol']
    lint['count'] = TBD_STR
    prop = 'meshlint_check_' + sym
    lint['check_prop'] = prop
    'meshlint_check_' + sym
    setattr(
        bpy.types.Scene,
        prop,
        bpy.props.BoolProperty(default=lint['default'])
    )

bl_info = {
    'name': 'Mesh Lint: Scrutinize Mesh Quality',
    'author': 'rking',
    'version': (1, 0),
    'blender': (2, 6, 3),
    'location': 'Object Data properties > ' + SUBPANEL_LABEL,
    'description': 'Check a mesh for: ' + LINTS_LIST,
    'warning': '',
    'wiki_url': '', # TODO
    'tracker_url': '', # TODO
    'category': 'Mesh' }

def should_show(context):
    obj = context.active_object 
    return obj and 'MESH' == obj.type


class MeshLintSelector(bpy.types.Operator):
    "Uncheck boxes below to prevent those checks from running."
    bl_idname = 'meshlint.select'
    bl_label = "Mesh Lint"

    @classmethod
    def poll(cls, context):
        return should_show(context)

    def execute(self, context):
        obj = context.active_object
        self.ensure_edit_mode()
        self.select_none()
        b = bmesh.from_edit_mesh(obj.data)
        self.enable_anything_select_mode(b)
        for lint in LINTS:
            sym = lint['symbol']
            should_check = getattr(context.scene, lint['check_prop'])
            if not should_check:
                lint['count'] = N_A_STR
                continue
            lint['count'] = 0
            method_name = 'check_' + sym
            method = getattr(type(self), method_name)
            bad = method(self, b)
            for elemtype in 'verts', 'edges', 'faces':
                indices = bad.get(elemtype, [])
                # maybe filter out hidden elements?
                bmseq = getattr(b, elemtype)
                for i in indices:
                    bmseq[i].select = True
                lint['count'] += len(indices)

        context.area.tag_redraw()
        return {'FINISHED'}

    def ensure_edit_mode(self):
        if 'EDIT_MESH' != bpy.context.mode:
            bpy.ops.object.editmode_toggle()

    def enable_anything_select_mode(self, b):
        b.select_mode = {'VERT', 'EDGE', 'FACE'}

    def select_none(self):
        bpy.ops.mesh.select_all(action='DESELECT')

    def check_nonmanifold(self, b):
        bad = {}
        for elemtype in 'verts', 'edges':
            bad[elemtype] = []
            for elem in getattr(b, elemtype):
                if not elem.is_manifold:
                    bad[elemtype].append(elem.index)
        print("MeshLint TODO: Deselect mirror-plane verts.")
        # ...anybody wanna tackle Mirrors with an Object Offset?
        return bad

    def check_tris(self, b):
        bad = { 'faces': [] }
        for f in b.faces:
            if 3 == len(f.verts):
                bad['faces'].append(f.index)
        return bad

    def check_ngons(self, b):
        bad = { 'faces': [] }
        for f in b.faces:
            if 4 < len(f.verts):
                bad['faces'].append(f.index)
        return bad

    def check_interior_faces(self, b): # translated from editmesh_select.c
        bad = { 'faces': [] }
        for f in b.faces:
            if not any(3 > len(e.link_faces) for e in f.edges):
                bad['faces'].append(f.index)
        return bad

    def check_sixplus_poles(self, b):
        bad = { 'verts': [] }
        for v in b.verts:
            if 5 < len(v.link_edges):
                bad['verts'].append(v.index)
        return bad
                

class MeshLintControl(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'
    bl_label = SUBPANEL_LABEL

    def draw(self, context):
        active = context.active_object
        layout = self.layout
        col = layout.column()
        col.operator('meshlint.select', text='Select Lint', icon='EDITMODE_HLT')
        # col.operator('meshlint.enliven', text='Continuous', icon='PLAY')
        # icon='PAUSE'

        if not should_show(context):
            return
        for lint in LINTS:
            count = lint['count']
            if count in (TBD_STR, N_A_STR):
                label = str(count) + ' ' + lint['label']
                reward = 'SOLO_OFF'
            elif 0 == count:
                label = 'No %s!' % lint['label']
                reward = 'SOLO_ON'
            else:
                label = str(count) + 'x ' + lint['label']
                if 1 == count:
                    label = label.rstrip('s')
                reward = 'ERROR'
            row = col.row()
            row.prop(context.scene, lint['check_prop'], text='')
            row.label(label, icon=reward)
        if self.has_bad_name(active.name):
            col.row().label(
                '...and you should think about renaming "%s"' % active.name
            )

    def has_bad_name(self, name):
        default_names = [
            'BezierCircle',
            'BezierCurve',
            'Circle',
            'Cone',
            'Cube',
            'CurvePath',
            'Cylinder',
            'Grid',
            'Icosphere',
            'Mball',
            'Monkey',
            'NurbsCircle',
            'NurbsCurve',
            'NurbsPath',
            'Plane',
            'Sphere',
            'Surface',
            'SurfCircle',
            'SurfCurve',
            'SurfCylinder',
            'SurfPatch',
            'SurfSphere',
            'SurfTorus',
            'Text',
        ]
        pat = '(%s).?\d*$' % '|'.join(default_names)
        return re.match(pat, name)
           

def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == '__main__':
    register()

# vim:ts=4 sw=4 sts=4
