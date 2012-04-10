bl_info = {
    'name': 'MeshLint: Scrutinize Mesh Quality',
    'author': 'rking',
    'version': (0, 8),
    'blender': (2, 6, 3),
    'location': 'Object Data properties > MeshLint',
    'description': 'Check a mesh for: Tris / Ngons / Nonmanifoldness / etc',
    'warning': '',
    'wiki_url': '',
    'tracker_url': '',
    'category': 'Mesh' }

import bpy
import bmesh
import time
import re

SUBPANEL_LABEL = 'MeshLint'

CHECKS = [
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

  # Plus 'Default Name'

  # [Your great new idea here] -> Tell me about it: rking@panoptic.com
]

ELEM_TYPES = [ 'verts', 'edges', 'faces' ]

N_A_STR = '(N/A - disabled)'
TBD_STR = '...'

for lint in CHECKS:
    sym = lint['symbol']
    lint['count'] = TBD_STR
    prop = 'meshlint_check_' + sym
    lint['check_prop'] = prop
    'meshlint_check_' + sym
    # TODO - blank previous_analysis on_change (fixes unexpected behavior
    # where checking/unchecking things does not update the counts/icons)
    setattr(
        bpy.types.Scene,
        prop,
        bpy.props.BoolProperty(default=lint['default']))

class MeshLintAnalyzer:
    def __init__(self):
        self.obj = bpy.context.active_object
        self.ensure_edit_mode()
        self.b = bmesh.from_edit_mesh(self.obj.data)

    def find_problems(self):
        analysis = [] 
        for lint in CHECKS:
            sym = lint['symbol']
            should_check = getattr(bpy.context.scene, lint['check_prop'])
            if not should_check:
                lint['count'] = N_A_STR
                continue
            lint['count'] = 0
            check_method_name = 'check_' + sym
            check_method = getattr(type(self), check_method_name)
            bad = check_method(self)
            report = { 'lint': lint }
            for elemtype in ELEM_TYPES:
                indices = bad.get(elemtype, [])
                report[elemtype] = indices
                lint['count'] += len(indices)
            analysis.append(report)
        return analysis

    @classmethod
    def none_analysis(cls):
        analysis = []
        for lint in CHECKS:
            row = { elemtype: [] for elemtype in ELEM_TYPES }
            row['lint'] = lint
            analysis.append(row)
        return analysis

    def ensure_edit_mode(self):
        if 'EDIT_MESH' != bpy.context.mode:
            bpy.ops.object.editmode_toggle()

    def check_nonmanifold(self):
        bad = {}
        for elemtype in 'verts', 'edges':
            bad[elemtype] = []
            for elem in getattr(self.b, elemtype):
                if not elem.is_manifold:
                    bad[elemtype].append(elem.index)
        # TODO: Exempt mirror-plane verts.
        # Plus: ...anybody wanna tackle Mirrors with an Object Offset?
        return bad

    def check_tris(self):
        bad = { 'faces': [] }
        for f in self.b.faces:
            if 3 == len(f.verts):
                bad['faces'].append(f.index)
        return bad

    def check_ngons(self):
        bad = { 'faces': [] }
        for f in self.b.faces:
            if 4 < len(f.verts):
                bad['faces'].append(f.index)
        return bad

    def check_interior_faces(self): # translated from editmesh_select.c
        bad = { 'faces': [] }
        for f in self.b.faces:
            if not any(3 > len(e.link_faces) for e in f.edges):
                bad['faces'].append(f.index)
        return bad

    def check_sixplus_poles(self):
        bad = { 'verts': [] }
        for v in self.b.verts:
            if 5 < len(v.link_edges):
                bad['verts'].append(v.index)
        return bad

    def enable_anything_select_mode(self):
        self.b.select_mode = {'VERT', 'EDGE', 'FACE'}

    def select_indices(self, elemtype, indices):
        bmseq = getattr(self.b, elemtype)
        for i in indices:
            # TODO: maybe filter out hidden elements?
            bmseq[i].select = True

    def topology_counts(self):
        # XXX - Is this protected so it only runs with meshes? I don't know
        data = self.obj.data
        return {
            'data': self.obj.data,
            'faces': len(self.b.faces),
            'edges': len(self.b.edges),
            'verts': len(self.b.verts) }


def has_active_mesh(context):
    obj = context.active_object 
    return obj and 'MESH' == obj.type

@bpy.app.handlers.persistent
def global_repeated_check(dummy):
    MeshLintContinuousChecker.check()

class MeshLintContinuousChecker():
    current_message = ''
    message_displayed_at = 0
    previous_topology_counts = None
    previous_analysis = None

    @classmethod
    def check(cls):
        if 'EDIT_MESH' != bpy.context.mode:
            return
        analyzer = MeshLintAnalyzer()
        now_counts = analyzer.topology_counts()
        previous_topology_counts = \
            MeshLintContinuousChecker.previous_topology_counts
        if not None is previous_topology_counts:
            previous_data_name = previous_topology_counts['data'].name
        else:
            previous_data_name = None
        now_name = now_counts['data'].name
        if None is previous_topology_counts \
                or now_counts != previous_topology_counts:
            if not previous_data_name == now_name:
                before = MeshLintAnalyzer.none_analysis()
            analysis = analyzer.find_problems()
            diff_msg = MeshLintContinuousChecker.diff_analyses(
                MeshLintContinuousChecker.previous_analysis, analysis)
            if not None is diff_msg:
                MeshLintContinuousChecker.current_message = diff_msg
                MeshLintContinuousChecker.message_displayed_at = time.time()
            MeshLintContinuousChecker.previous_topology_counts = now_counts
            MeshLintContinuousChecker.previous_analysis = analysis
        if 3 < time.time() - MeshLintContinuousChecker.message_displayed_at:
            MeshLintContinuousChecker.current_message = ''

    @classmethod
    def diff_analyses(cls, before, after):
        if None is before:
            before = MeshLintAnalyzer.none_analysis()
        report_strings = []
        dict_before = MeshLintContinuousChecker.make_labels_dict(before)
        dict_now = MeshLintContinuousChecker.make_labels_dict(after)
        for check in CHECKS:
            check_name = check['label']
            if not check_name in dict_now.keys():
                continue
            report = dict_now[check_name]
            report_before = dict_before.get(check_name, {})
            check_elem_strings = []
            for elemtype, elem_list in report.items():
                elem_list_before = report_before.get(elemtype, [])
                if len(elem_list) > len(elem_list_before):
                    count_diff = len(elem_list) - len(elem_list_before)
                    elem_string = depluralize(count=count_diff, string=elemtype)
                    check_elem_strings.append(
                        str(count_diff) + ' ' + elem_string)
            if len(check_elem_strings):
                report_strings.append(
                    check_name + ': ' + ', '.join(check_elem_strings))
        if len(report_strings):
            return 'Found ' + ', '.join(report_strings)
        return None

    @classmethod
    def make_labels_dict(cls, analysis):
        if None is analysis:
            return {}
        labels_dict = {}
        for check in analysis:
            label = check['lint']['label']
            new_val = check.copy()
            del new_val['lint']
            labels_dict[label] = new_val
        return labels_dict

class MeshLintVitalizer(bpy.types.Operator):
    'Toggles the real-time execution of the checks'
    bl_idname = 'meshlint.live_toggle'
    bl_label = 'MeshLint Live Toggle'

    is_live = False

    @classmethod
    def poll(cls, context):
        return has_active_mesh(context) and 'EDIT_MESH' == bpy.context.mode

    def execute(self, context):
        if MeshLintVitalizer.is_live:
            bpy.app.handlers.scene_update_post.remove(global_repeated_check)
            MeshLintVitalizer.is_live = False
        else:
            bpy.app.handlers.scene_update_post.append(global_repeated_check)
            MeshLintVitalizer.is_live = True
        return {'FINISHED'}

class MeshLintSelector(bpy.types.Operator):
    'Uncheck boxes below to prevent those checks from running'
    bl_idname = 'meshlint.select'
    bl_label = 'MeshLint Select'

    @classmethod
    def poll(cls, context):
        return has_active_mesh(context)

    def execute(self, context):
        analyzer = MeshLintAnalyzer()
        analyzer.enable_anything_select_mode()
        self.select_none()
        analysis = analyzer.find_problems()
        for lint in analysis:
            for elemtype in ELEM_TYPES:
                indices = lint[elemtype]
                analyzer.select_indices(elemtype, indices)
        # TODO Note. This doesn't quite get it done. I don't know if it's a
        # problem in my script or in the redraw, but sometimes you have to
        # move the 3D View to get the selection to show. =( I need to first
        # figure out the exact circumstances that cause it, then go about
        # debugging.
        context.area.tag_redraw()
        # Record this so the first time the user hits "Continuous Check!" it
        # doesn't spew out info they already knew:
        MeshLintContinuousChecker.previous_analysis = analysis
        return {'FINISHED'}

    def select_none(self):
        bpy.ops.mesh.select_all(action='DESELECT')
                

class MeshLintControl(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'
    bl_label = SUBPANEL_LABEL

    def draw(self, context):
        layout = self.layout
        self.maybe_add_now_you_done_it_text(layout)
        self.add_main_buttons(layout)
        if 'EDIT_MESH' == bpy.context.mode:
            self.add_rows(layout, context)

    def maybe_add_now_you_done_it_text(self, layout):
        col = layout.column()
        msg = MeshLintContinuousChecker.current_message
        if not '' == msg:
            col.label(msg, icon='ERROR')

    def add_main_buttons(self, layout):
        split = layout.split()
        left = split.column()
        left.operator(
            'meshlint.select', text='Select Lint', icon='EDITMODE_HLT')

        right = split.column()
        if MeshLintVitalizer.is_live:
            live_label = 'Pause Checking...'
            play_pause = 'PAUSE'
        else:
            live_label = 'Continuous Check!'
            play_pause = 'PLAY'
        right.operator('meshlint.live_toggle', text=live_label, icon=play_pause)

    def add_rows(self, layout, context):
        col = layout.column()
        active = context.active_object
        if not has_active_mesh(context):
            return
        for lint in CHECKS:
            count = lint['count']
            if count in (TBD_STR, N_A_STR):
                label = str(count) + ' ' + lint['label']
                reward = 'SOLO_OFF'
            elif 0 == count:
                label = 'No %s!' % lint['label']
                reward = 'SOLO_ON'
            else:
                label = str(count) + 'x ' + lint['label']
                label = depluralize(count=count, string=label)
                reward = 'ERROR'
            row = col.row()
            row.prop(context.scene, lint['check_prop'], text=label, icon=reward)
        if MeshLintControl.has_bad_name(active.name):
            col.row().label(
                '...and "%s" is not a great name, BTW.' % active.name)

    @classmethod
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
        pat = '(%s)\.?\d*$' % '|'.join(default_names)
        return not None is re.match(pat, name)


def depluralize(**args):
    if 1 == args['count']:
        return args['string'].rstrip('s')
    else:
        return args['string']
           

def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)


# Hrm. Why does it work for some Blender's but not others?
try:

    import unittest
    import warnings

    class TestControl(unittest.TestCase):
        def test_bad_names(self):
            for bad in [ 'Cube', 'Cube.001', 'Sphere.123' ]:
                self.assertEqual(
                    True, MeshLintControl.has_bad_name(bad),
                    "Bad name: %s" % bad)
            for ok in [ 'Whatever', 'NumbersOkToo.001' ]:
                self.assertEqual(
                    False, MeshLintControl.has_bad_name(ok),
                    "OK name: %s" % ok)

    class TestUtilities(unittest.TestCase):
        def test_depluralize(self):
            self.assertEqual(
                'foo',
                depluralize(count=1, string='foos'))
            self.assertEqual(
                'foos',
                depluralize(count=2, string='foos'))


    class TestAnalysis(unittest.TestCase):
        def test_make_labels_dict(self):
            self.assertEqual(
                {
                    'Label One': { 'edges': [1,2], 'verts': [], 'faces': [] },
                    'Label Two': { 'edges': [], 'verts': [5], 'faces': [3] }
                },
                MeshLintContinuousChecker.make_labels_dict(
                    [
                        { 'lint': { 'label': 'Label One' },
                            'edges': [1,2], 'verts': [], 'faces': [] },
                        { 'lint': { 'label': 'Label Two' },
                            'edges': [], 'verts': [5], 'faces': [3] }
                    ]),
                'Conversion of incoming analysis into label-keyed dict')
            self.assertEqual(
                {},
                MeshLintContinuousChecker.make_labels_dict(None),
                'Handles "None" OK.')

        def test_comparison(self):
            self.assertEqual(
                None,
                MeshLintContinuousChecker.diff_analyses(
                    MeshLintAnalyzer.none_analysis(),
                    MeshLintAnalyzer.none_analysis()),
                'Two none_analysis()s')
            self.assertEqual(
                'Found Tris: 4 verts',
                MeshLintContinuousChecker.diff_analyses(
                    None,
                    [
                        {
                            'lint': { 'label': 'Tris' },
                            'verts': [1,2,3,4],
                            'edges': [],
                            'faces': [],
                        },
                    ]),
                'When there was no previous analysis')
            self.assertEqual(
                'Found Tris: 2 edges, Nonmanifold Elements: 4 verts, 1 face',
                MeshLintContinuousChecker.diff_analyses(
                    [
                        { 'lint': { 'label': 'Tris' },
                          'verts': [], 'edges': [1,4], 'faces': [], },
                        { 'lint': { 'label': 'CheckB' },
                          'verts': [], 'edges': [2,3], 'faces': [], },
                        { 'lint': { 'label': 'Nonmanifold Elements' },
                          'verts': [], 'edges': [], 'faces': [2,3], },
                    ],
                    [
                        { 'lint': { 'label': 'Tris' },
                          'verts': [], 'edges': [1,4,5,6], 'faces': [], },
                        { 'lint': { 'label': 'CheckB' },
                          'verts': [], 'edges': [2,3], 'faces': [], },
                        { 'lint': { 'label': 'Nonmanifold Elements' },
                          'verts': [1,2,3,4], 'edges': [], 'faces': [2,3,5], },
                    ]),
                'Complex comparison of analyses')
            self.assertEqual(
                'Found Tris: 1 vert, Ngons: 2 faces, ' + 
                  'Nonmanifold Elements: 2 edges',
                MeshLintContinuousChecker.diff_analyses(
                    [
                        { 'lint': { 'label': '6+-edge Poles' },
                          'verts': [], 'edges': [2,3], 'faces': [], },
                        { 'lint': { 'label': 'Nonmanifold Elements' },
                          'verts': [], 'edges': [2,3], 'faces': [], },
                    ],
                    [
                        { 'lint': { 'label': 'Tris' },
                          'verts': [55], 'edges': [], 'faces': [], },
                        { 'lint': { 'label': 'Ngons' },
                          'verts': [], 'edges': [], 'faces': [5,6], },
                        { 'lint': { 'label': 'Nonmanifold Elements' },
                          'verts': [], 'edges': [2,3,4,5], 'faces': [], },
                    ]),
                'User picked a different set of checks since last run.')

    class QuietOnSuccessTestresult(unittest.TextTestResult):
        def startTest(self, test):
            pass

        def addSuccess(self, test):
            pass


    class QuietTestRunner(unittest.TextTestRunner):
        resultclass = QuietOnSuccessTestresult

        # Ugh. I really shouldn't have to include this much code, but they
        # left it so unrefactored I don't know what else to do. My other
        # option is to override the stream and substitute out the success
        # case, but that's a mess, too. - rking
        def run(self, test):
            "Run the given test case or test suite."
            result = self._makeResult()
            unittest.registerResult(result)
            result.failfast = self.failfast
            result.buffer = self.buffer
            with warnings.catch_warnings():
                if self.warnings:
                    # if self.warnings is set, use it to filter all the warnings
                    warnings.simplefilter(self.warnings)
                    # if the filter is 'default' or 'always', special-case the
                    # warnings from the deprecated unittest methods to show them
                    # no more than once per module, because they can be fairly
                    # noisy.  The -Wd and -Wa flags can be used to bypass this
                    # only when self.warnings is None.
                    if self.warnings in ['default', 'always']:
                        warnings.filterwarnings('module',
                                category=DeprecationWarning,
                                message='Please use assert\w+ instead.')
                startTime = time.time()
                startTestRun = getattr(result, 'startTestRun', None)
                if startTestRun is not None:
                    startTestRun()
                try:
                    test(result)
                finally:
                    stopTestRun = getattr(result, 'stopTestRun', None)
                    if stopTestRun is not None:
                        stopTestRun()
                stopTime = time.time()
            timeTaken = stopTime - startTime
            result.printErrors()
            run = result.testsRun

            expectedFails = unexpectedSuccesses = skipped = 0
            try:
                results = map(len, (result.expectedFailures,
                                    result.unexpectedSuccesses,
                                    result.skipped))
            except AttributeError:
                pass
            else:
                expectedFails, unexpectedSuccesses, skipped = results

            infos = []
            if not result.wasSuccessful():
                self.stream.write("FAILED")
                failed, errored = len(result.failures), len(result.errors)
                if failed:
                    infos.append("failures=%d" % failed)
                if errored:
                    infos.append("errors=%d" % errored)
            if skipped:
                infos.append("skipped=%d" % skipped)
            if expectedFails:
                infos.append("expected failures=%d" % expectedFails)
            if unexpectedSuccesses:
                infos.append("unexpected successes=%d" % unexpectedSuccesses)
            return result

    if __name__ == '__main__':
        unittest.main(
            testRunner=QuietTestRunner, argv=['dummy'], exit=False, verbosity=0)

except ImportError:
    print("MeshLint complains over missing unittest module. No harm, only odd.")

if __name__ == '__main__':
    register()

# vim:ts=4 sw=4 sts=4
