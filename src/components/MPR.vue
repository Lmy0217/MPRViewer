<template>
    <div class="con">
        <div class="config">
            <table>
                <tr>
                    <td>
                        <input type="file" id="file" accept=".vti,.nii.gz" hidden/>
                        <button class="btn btn-info" id="btnLoad">Choose file</button>
                    </td>
                    <td>
                        <label class="label">{{filename}}</label>
                    </td>
                </tr>
                <tr>
                    <td>Allow translation:</td>
                    <td>
                        <input type="checkbox" id="checkboxTranslation" checked>
                    </td>
                </tr>
                <tr>
                    <td>Show rotation:</td>
                    <td>
                        <input type="checkbox" id="checkboxShowRotation" checked>
                    </td>
                </tr>
                <tr>
                    <td>Allow rotation:</td>
                    <td>
                        <input type="checkbox" id="checkboxRotation" checked>
                    </td>
                </tr>
                <tr>
                    <td>Keep orthogonality:</td>
                    <td>
                        <input type="checkbox" id="checkboxOrthogonality" checked>
                    </td>
                </tr>
                <tr>
                    <td>Scale in pixels:</td>
                    <td>
                        <input type="checkbox" id="checkboxScaleInPixels" checked>
                    </td>
                </tr>
                <tr>
                    <td>Opacity:</td>
                    <td><input id='opacity' type="range" min="0" max="255" step="1" value="255" style="width: 100px;"/>
                    </td>
                    <td id='opacityValue'>255</td>
                </tr>
                <tr>
                    <td>Slab Mode:</td>
                    <td>
                        <select id="slabMode">
                            <option id="slabModeMin">MIN</option>
                            <option id="slabModeMax">MAX</option>
                            <option id="slabModeMean" selected="selected">MEAN</option>
                            <option id="slabModeSum">SUM</option>
                        </select>
                    </td>
                </tr>
                <tr>
                    <td>Slab Number of Slices:</td>
                    <td><input id='slabNumber' type="range" min="1" max="100" step="1" value="1" style="width: 100px;"/>
                    </td>
                    <td id='slabNumberValue'>1</td>
                </tr>
                <tr>
                    <td>Interpolation mode:</td>
                    <td>
                        <select id="selectInterpolation">
                            <option id="nearest" selected="selected">Nearest</option>
                            <option id="linear">Linear</option>
                        </select>
                    </td>
                </tr>
                <tr>
                    <td>Window Level:</td>
                    <td>
                        <input type="checkbox" id="checkboxWindowLevel" checked>
                    </td>
                </tr>
                <tr>
                    <td>
                        <button id="buttonReset">Reset views</button>
                    </td>
                </tr>
                <tr>
                    <td>Shape:</td>
                    <td id="shapeValue">null</td>
                </tr>
                <tr>
                    <td>Spacing-X:</td>
                    <td id="spacingXValue">null</td>
                </tr>
                <tr>
                    <td>Spacing-Y:</td>
                    <td id="spacingYValue">null</td>
                </tr>
                <tr>
                    <td>Spacing-Z:</td>
                    <td id="spacingZValue">null</td>
                </tr>
            </table>
        </div>
        <div class="render">
            <div id="v1" class="view"/>
            <div id="v2" class="view"/>
            <div id="v3" class="view"/>
            <div id="v4" class="view"/>
        </div>
    </div>
</template>

<script setup>
// Load the rendering pieces we want to use (for both WebGL and WebGPU)
import '@kitware/vtk.js/Rendering/Profiles/All';

import vtkActor from '@kitware/vtk.js/Rendering/Core/Actor';
import vtkAnnotatedCubeActor from '@kitware/vtk.js/Rendering/Core/AnnotatedCubeActor';
import vtkHttpDataSetReader from '@kitware/vtk.js/IO/Core/HttpDataSetReader';
import vtkGenericRenderWindow from '@kitware/vtk.js/Rendering/Misc/GenericRenderWindow';
import vtkImageMapper from '@kitware/vtk.js/Rendering/Core/ImageMapper';
import vtkImageReslice from '@kitware/vtk.js/Imaging/Core/ImageReslice';
import vtkImageSlice from '@kitware/vtk.js/Rendering/Core/ImageSlice';
import vtkInteractorStyleImage from '@kitware/vtk.js/Interaction/Style/InteractorStyleImage';
import vtkInteractorStyleTrackballCamera from '@kitware/vtk.js/Interaction/Style/InteractorStyleTrackballCamera';
import vtkMapper from '@kitware/vtk.js/Rendering/Core/Mapper';
import vtkOutlineFilter from '@kitware/vtk.js/Filters/General/OutlineFilter';
import vtkOrientationMarkerWidget from '@kitware/vtk.js/Interaction/Widgets/OrientationMarkerWidget';
import vtkResliceCursorWidget from '@kitware/vtk.js/Widgets/Widgets3D/ResliceCursorWidget';
import vtkWidgetManager from '@kitware/vtk.js/Widgets/Core/WidgetManager';

import vtkSphereSource from '@kitware/vtk.js/Filters/Sources/SphereSource';
import {CaptureOn} from '@kitware/vtk.js/Widgets/Core/WidgetManager/Constants';

import {vec3} from 'gl-matrix';
import {SlabMode} from '@kitware/vtk.js/Imaging/Core/ImageReslice/Constants';

import {xyzToViewType} from '@kitware/vtk.js/Widgets/Widgets3D/ResliceCursorWidget/Constants';

import '@kitware/vtk.js/IO/Core/DataAccessHelper/HttpDataAccessHelper';

import {onBeforeUnmount, onMounted, ref} from 'vue';
import vtkVolumeMapper from "@kitware/vtk.js/Rendering/Core/VolumeMapper";
import vtkVolume from "@kitware/vtk.js/Rendering/Core/Volume";
import vtkBoundingBox from "@kitware/vtk.js/Common/DataModel/BoundingBox";
import vtkColorTransferFunction from "@kitware/vtk.js/Rendering/Core/ColorTransferFunction";
import vtkPiecewiseFunction from "@kitware/vtk.js/Common/DataModel/PiecewiseFunction";
import vtkXMLImageDataReader from "@kitware/vtk.js/IO/XML/XMLImageDataReader";
import {arrayMax} from "@kitware/vtk.js/Common/Core/Math";
import {ElLoading} from "element-plus";

import {QWebChannel} from "qwebchannel";

let bridge = null;
let socket = null;

function create_bridge() {
    const address = 'ws://localhost:12345';
    socket = new WebSocket(address);

    socket.onopen = function() {
        console.log('WebSocket connected, setting up QWebChannel.');
        new QWebChannel(socket, (channel) => {
            bridge = channel.objects.bridge;
            bridge.send_data.connect((msg) => {
                start_loading();
                const textEncoder = new TextEncoder();
                update_file(textEncoder.encode(msg));
                stop_loading();
            });
            bridge.set_status(true);
        });
    };

    socket.onerror =function(error) {
        console.error('web channel error: ' + error.message);
    };

    socket.onclose = function() {
        console.log('web channel closed');
    };
}

function delete_bridge() {
    bridge = null;
    if (socket) {
        socket.close();
        socket = null;
    }
}

const viewColors = [
  [1, 0, 0], // sagittal
  [0, 1, 0], // coronal
  [0, 0, 1], // axial
  [0.5, 0.5, 0.5], // 3D
];

const lookupTable1 = vtkColorTransferFunction.newInstance();
lookupTable1.addRGBPoint(0, 85 / 255.0, 0, 0);
lookupTable1.addRGBPoint(95, 1.0, 1.0, 1.0);
lookupTable1.addRGBPoint(225, 0.66, 0.66, 0.5);
lookupTable1.addRGBPoint(255, 0.3, 1.0, 0.5);
const piecewiseFunction1 = vtkPiecewiseFunction.newInstance();
piecewiseFunction1.addPoint(0.0, 0.0);
piecewiseFunction1.addPoint(255.0, 1.0);

const lookupTable2 = vtkColorTransferFunction.newInstance();
lookupTable2.addRGBSegment(0, 0.0, 0.0, 1.0, 255.0, 1.0, 1.0, 1.0);
const piecewiseFunction2 = vtkPiecewiseFunction.newInstance();
const opacityWindow = 4096;
const opacityLevel = 2048;
piecewiseFunction2.addSegment(opacityLevel - 0.5 * opacityWindow, 0.0, opacityLevel + 0.5 * opacityWindow, 1.0);

function createRGBStringFromRGBValues(rgb) {
    if (rgb.length !== 3) {
        return 'rgb(0, 0, 0)';
    }
    return `rgb(${(rgb[0] * 255).toString()}, ${(rgb[1] * 255).toString()}, ${(rgb[2] * 255).toString()})`;
}

const context = ref(null);
let loading = null;
const loading_text = ref('Loading ...');
let filename = ref('No file chosen');

function checkboxTranslationEvent() {
    const { viewAttributes } = context.value;
    const checkboxTranslation = document.getElementById('checkboxTranslation');
    viewAttributes.forEach((obj) =>
        obj.widgetInstance.setEnableTranslation(checkboxTranslation.checked)
    );
}

function checkboxOrthogonalityEvent() {
    const checkboxOrthogonality = document.getElementById('checkboxOrthogonality');
    const { viewAttributes } = context.value;
    viewAttributes.forEach((obj) =>
        obj.widgetInstance.setKeepOrthogonality(checkboxOrthogonality.checked)
    );
}

function checkboxRotationEvent() {
    const checkboxRotation = document.getElementById('checkboxRotation');
    const checkboxOrthogonality = document.getElementById('checkboxOrthogonality');
    const { viewAttributes } = context.value;
    viewAttributes.forEach((obj) =>
        obj.widgetInstance.setEnableRotation(checkboxRotation.checked)
    );
    checkboxOrthogonality.disabled = !checkboxRotation.checked;
    checkboxOrthogonality.dispatchEvent(new Event('change'));
}

function checkboxShowRotationEvent() {
    const { widgetState, viewAttributes } = context.value;
    const checkboxShowRotation = document.getElementById('checkboxShowRotation');
    const checkboxRotation = document.getElementById('checkboxRotation');
    widgetState.getStatesWithLabel('rotation').forEach(
        (handle) => handle.setVisible(checkboxShowRotation.checked)
    );
    viewAttributes.forEach((obj) => {
        obj.interactor.render();
    });
    checkboxRotation.checked = checkboxShowRotation.checked;
    checkboxRotation.disabled = !checkboxShowRotation.checked;
    checkboxRotation.dispatchEvent(new Event('change'));
}

function checkboxScaleInPixelsEvent() {
    const { widget, viewAttributes } = context.value;
    const checkboxScaleInPixels = document.getElementById('checkboxScaleInPixels');
    widget.setScaleInPixels(checkboxScaleInPixels.checked);
    viewAttributes.forEach((obj) => {
        obj.interactor.render();
    });
}

function opacityEvent(ev) {
    const { widget, viewAttributes } = context.value;
    const opacityValue = document.getElementById('opacityValue');
    opacityValue.innerHTML = ev.target.value;
    widget.getWidgetState().getStatesWithLabel('handles').forEach(
        (handle) => handle.setOpacity(ev.target.value)
    );
    viewAttributes.forEach((obj) => {
        obj.interactor.render();
    });
}

function selectSlabModeEvent(ev) {
    const { viewAttributes } = context.value;
    viewAttributes.forEach((obj) => {
        obj.reslice.setSlabMode(Number(ev.target.value));
    });
    updateViews();
}

function sliderSlabNumberofSlicesEvent(ev) {
    const { viewAttributes } = context.value;
    const trSlabNumberValue = document.getElementById('slabNumberValue');
    trSlabNumberValue.innerHTML = ev.target.value;
    viewAttributes.forEach((obj) => {
        obj.reslice.setSlabNumberOfSlices(ev.target.value);
    });
    updateViews();
}

function selectInterpolationModeEvent(ev) {
    const { viewAttributes } = context.value;
    viewAttributes.forEach((obj) => {
        obj.reslice.setInterpolationMode(Number(ev.target.selectedIndex));
    });
    updateViews();
}

function buttonResetEvent() {
    const { widget, widgetState, initialPlanesState } = context.value;
    widgetState.setPlanes({ ...initialPlanesState });
    widget.setCenter(widget.getWidgetState().getImage().getCenter());
    updateViews();
}

function checkboxWindowLevelEvent() {
    const checkboxWindowLevel = document.getElementById('checkboxWindowLevel');
    const { viewAttributes } = context.value;
    viewAttributes.forEach((obj, index) => {
        if (index < 3) {
            obj.interactor.setInteractorStyle(
                checkboxWindowLevel.checked
                    ? vtkInteractorStyleImage.newInstance()
                    : vtkInteractorStyleTrackballCamera.newInstance()
            );
        }
    });
}

function btnLoadEvent() {
    document.getElementById('file').click();
}

function add_event_listeners() {
    const checkboxTranslation = document.getElementById('checkboxTranslation');
    checkboxTranslation.addEventListener('change', checkboxTranslationEvent);

    const checkboxOrthogonality = document.getElementById('checkboxOrthogonality');
    checkboxOrthogonality.addEventListener('change', checkboxOrthogonalityEvent);

    const checkboxRotation = document.getElementById('checkboxRotation');
    checkboxRotation.addEventListener('change', checkboxRotationEvent);

    const checkboxShowRotation = document.getElementById('checkboxShowRotation');
    checkboxShowRotation.addEventListener('change', checkboxShowRotationEvent);

    const checkboxScaleInPixels = document.getElementById('checkboxScaleInPixels');
    checkboxScaleInPixels.addEventListener('change', checkboxScaleInPixelsEvent);

    const opacity = document.getElementById('opacity');
    opacity.addEventListener('input', opacityEvent);

    const optionSlabModeMin = document.getElementById('slabModeMin');
    optionSlabModeMin.value = SlabMode.MIN;
    const optionSlabModeMax = document.getElementById('slabModeMax');
    optionSlabModeMax.value = SlabMode.MAX;
    const optionSlabModeMean = document.getElementById('slabModeMean');
    optionSlabModeMean.value = SlabMode.MEAN;
    const optionSlabModeSum = document.getElementById('slabModeSum');
    optionSlabModeSum.value = SlabMode.SUM;
    const selectSlabMode = document.getElementById('slabMode');
    selectSlabMode.addEventListener('change', selectSlabModeEvent);

    const sliderSlabNumberofSlices = document.getElementById('slabNumber');
    sliderSlabNumberofSlices.addEventListener('change', sliderSlabNumberofSlicesEvent);

    const selectInterpolationMode = document.getElementById('selectInterpolation');
    selectInterpolationMode.addEventListener('change', selectInterpolationModeEvent);

    const buttonReset = document.getElementById('buttonReset');
    buttonReset.addEventListener('click', buttonResetEvent);

    const checkboxWindowLevel = document.getElementById('checkboxWindowLevel');
    checkboxWindowLevel.addEventListener('change', checkboxWindowLevelEvent);

    const fileInput = document.getElementById('file');
    fileInput.addEventListener('change', load_file);

    const btnLoad = document.getElementById('btnLoad');
    btnLoad.addEventListener('click', btnLoadEvent);
}

function remove_event_listeners() {
    const checkboxTranslation = document.getElementById('checkboxTranslation');
    checkboxTranslation.removeEventListener('change', checkboxTranslationEvent);

    const checkboxOrthogonality = document.getElementById('checkboxOrthogonality');
    checkboxOrthogonality.removeEventListener('change', checkboxOrthogonalityEvent);

    const checkboxRotation = document.getElementById('checkboxRotation');
    checkboxRotation.removeEventListener('change', checkboxRotationEvent);

    const checkboxShowRotation = document.getElementById('checkboxShowRotation');
    checkboxShowRotation.removeEventListener('change', checkboxShowRotationEvent);

    const checkboxScaleInPixels = document.getElementById('checkboxScaleInPixels');
    checkboxScaleInPixels.removeEventListener('change', checkboxScaleInPixelsEvent);

    const opacity = document.getElementById('opacity');
    opacity.removeEventListener('input', opacityEvent);

    const selectSlabMode = document.getElementById('slabMode');
    selectSlabMode.removeEventListener('change', selectSlabModeEvent);

    const sliderSlabNumberofSlices = document.getElementById('slabNumber');
    sliderSlabNumberofSlices.removeEventListener('change', sliderSlabNumberofSlicesEvent);

    const selectInterpolationMode = document.getElementById('selectInterpolation');
    selectInterpolationMode.removeEventListener('change', selectInterpolationModeEvent);

    const buttonReset = document.getElementById('buttonReset');
    buttonReset.removeEventListener('click', buttonResetEvent);

    const checkboxWindowLevel = document.getElementById('checkboxWindowLevel');
    checkboxWindowLevel.removeEventListener('change', checkboxWindowLevelEvent);

    const fileInput = document.getElementById('file');
    fileInput.removeEventListener('change', load_file);

    const btnLoad = document.getElementById('btnLoad');
    btnLoad.removeEventListener('click', btnLoadEvent);
}

function create_context() {
    const viewAttributes = [];
    const widget = vtkResliceCursorWidget.newInstance();
    const widgetState = widget.getWidgetState();
    // Set size in CSS pixel space because scaleInPixels defaults to true
    widgetState.getStatesWithLabel('sphere').forEach((handle) => handle.setScale1(20));
    const showDebugActors = true;

    const initialPlanesState = {...widgetState.getPlanes()};

    let view3D = null;

    for (let i = 0; i < 4; i++) {
        const element = document.getElementById(`v${i + 1}`);

        const grw = vtkGenericRenderWindow.newInstance();
        grw.setContainer(element);
        grw.resize();

        const obj = {
            grw: grw,
            renderWindow: grw.getRenderWindow(),
            renderer: grw.getRenderer(),
            GLWindow: grw.getOpenGLRenderWindow(),
            interactor: grw.getInteractor(),
            widgetManager: vtkWidgetManager.newInstance(),
            orientationWidget: null,
        };
        obj.renderer.getActiveCamera().setParallelProjection(true);
        obj.renderer.setBackground(...viewColors[i]);
        obj.renderWindow.addRenderer(obj.renderer);
        obj.renderWindow.addView(obj.GLWindow);
        obj.interactor.setView(obj.GLWindow);
        obj.interactor.initialize();
        obj.interactor.bindEvents(element);
        obj.renderWindow.setInteractor(obj.interactor);

        obj.widgetManager.setRenderer(obj.renderer);
        if (i < 3) {
            obj.interactor.setInteractorStyle(vtkInteractorStyleImage.newInstance());
            obj.widgetInstance = obj.widgetManager.addWidget(widget, xyzToViewType[i]);
            obj.widgetInstance.setScaleInPixels(true);
            obj.widgetInstance.setKeepOrthogonality(true);
            obj.widgetManager.enablePicking();
            // Use to update all renderers buffer when actors are moved
            obj.widgetManager.setCaptureOn(CaptureOn.MOUSE_MOVE);
        } else {
            obj.interactor.setInteractorStyle(vtkInteractorStyleTrackballCamera.newInstance());
        }

        obj.reslice = vtkImageReslice.newInstance();
        obj.reslice.setSlabMode(SlabMode.MEAN);
        obj.reslice.setSlabNumberOfSlices(1);
        obj.reslice.setTransformInputSampling(false);
        obj.reslice.setAutoCropOutput(true);
        obj.reslice.setOutputDimensionality(2);
        obj.resliceMapper = vtkImageMapper.newInstance();
        obj.resliceMapper.setInputConnection(obj.reslice.getOutputPort());
        obj.resliceActor = vtkImageSlice.newInstance();
        obj.resliceActor.setMapper(obj.resliceMapper);

        // Create sphere for each 2D views which will be displayed in 3D
        // Define origin, point1 and point2 of the plane used to reslice the volume
        obj.sphereSources = [];
        obj.sphereMappers = [];
        obj.sphereActors = [];
        for (let j = 0; j < 3; j++) {
            const sphere = vtkSphereSource.newInstance();
            sphere.setRadius(10);
            const mapper = vtkMapper.newInstance();
            mapper.setInputConnection(sphere.getOutputPort());
            const actor = vtkActor.newInstance();
            actor.setMapper(mapper);
            actor.getProperty().setColor(...viewColors[i]);
            actor.setVisibility(showDebugActors);
            obj.sphereSources.push(sphere);
            obj.sphereMappers.push(mapper);
            obj.sphereActors.push(actor);
        }

        if (i < 3) {
            viewAttributes.push(obj);
        } else {
            view3D = obj;
        }

        // create axes
        const axes = vtkAnnotatedCubeActor.newInstance();
        axes.setDefaultStyle({
            text: '+X',
            fontStyle: 'bold',
            fontFamily: 'Arial',
            fontColor: 'black',
            fontSizeScale: (res) => res / 2,
            faceColor: createRGBStringFromRGBValues(viewColors[0]),
            faceRotation: 0,
            edgeThickness: 0.1,
            edgeColor: 'black',
            resolution: 400,
        });
        axes.setXMinusFaceProperty({
            text: '-X',
            faceColor: createRGBStringFromRGBValues(viewColors[0]),
        });
        axes.setYPlusFaceProperty({
            text: '+Y',
            faceColor: createRGBStringFromRGBValues(viewColors[1]),
        });
        axes.setYMinusFaceProperty({
            text: '-Y',
            faceColor: createRGBStringFromRGBValues(viewColors[1]),
        });
        axes.setZPlusFaceProperty({
            text: '+Z',
            faceColor: createRGBStringFromRGBValues(viewColors[2]),
        });
        axes.setZMinusFaceProperty({
            text: '-Z',
            faceColor: createRGBStringFromRGBValues(viewColors[2]),
        });
        obj.orientationAxes = axes

        // create orientation widget
        obj.orientationWidget = vtkOrientationMarkerWidget.newInstance({
            actor: axes,
            interactor: obj.renderWindow.getInteractor(),
        });
        obj.orientationWidget.setEnabled(true);
        obj.orientationWidget.setViewportCorner(vtkOrientationMarkerWidget.Corners.BOTTOM_RIGHT);
        obj.orientationWidget.setViewportSize(0.15);
        obj.orientationWidget.setMinPixelSize(50);
        obj.orientationWidget.setMaxPixelSize(150);
    }

    add_event_listeners();

    context.value = {
        widget,
        widgetState,
        initialPlanesState,
        viewAttributes,
        view3D,
    }
}

function updateReslice(
    interactionContext = {
        viewType: '',
        reslice: null,
        actor: null,
        renderer: null,
        resetFocalPoint: false, // Reset the focal point to the center of the display image
        keepFocalPointPosition: false, // Defines if the focal point position is kepts (same display distance from reslice cursor center)
        computeFocalPointOffset: false, // Defines if the display offset between reslice center and focal point has to be
        // computed. If so, then this offset will be used to keep the focal point position during rotation.
        spheres: null,
    }
) {
    const { widget, view3D } = context.value;
    const obj = widget.updateReslicePlane(
        interactionContext.reslice,
        interactionContext.viewType
    );
    if (obj.modified) {
        // Get returned modified from setter to know if we have to render
        interactionContext.actor.setUserMatrix(
            interactionContext.reslice.getResliceAxes()
        );
        interactionContext.sphereSources[0].setCenter(...obj.origin);
        interactionContext.sphereSources[1].setCenter(...obj.point1);
        interactionContext.sphereSources[2].setCenter(...obj.point2);
    }
    widget.updateCameraPoints(
        interactionContext.renderer,
        interactionContext.viewType,
        interactionContext.resetFocalPoint,
        interactionContext.keepFocalPointPosition,
        interactionContext.computeFocalPointOffset
    );
    view3D.renderWindow.render();
    return obj.modified;
}

function updateViews() {
    const { viewAttributes, view3D } = context.value;
    viewAttributes.forEach((obj, i) => {
        updateReslice({
            viewType: xyzToViewType[i],
            reslice: obj.reslice,
            actor: obj.resliceActor,
            renderer: obj.renderer,
            resetFocalPoint: true,
            keepFocalPointPosition: false,
            computeFocalPointOffset: true,
            sphereSources: obj.sphereSources,
            resetViewUp: true,
        });
        obj.renderWindow.render();
    });
    view3D.renderer.resetCamera();
    view3D.renderer.resetCameraClippingRange();
}

function update_data(image, lookupTable, piecewiseFunction) {
    const { widget, viewAttributes, view3D } = context.value;
    widget.setImage(image);

    const dimensions = image.getDimensions();
    const spacing = image.getSpacing();
    const shapeValue = document.getElementById('shapeValue');
    shapeValue.innerHTML = '(' + dimensions[0] + ', ' + dimensions[1] + ', ' + dimensions[2] + ')';
    const spacingXValue = document.getElementById('spacingXValue');
    spacingXValue.innerHTML = spacing[0].toFixed(4);
    const spacingYValue = document.getElementById('spacingYValue');
    spacingYValue.innerHTML = spacing[1].toFixed(4);
    const spacingZValue = document.getElementById('spacingZValue');
    spacingZValue.innerHTML = spacing[2].toFixed(4);

    const mapper = vtkVolumeMapper.newInstance();
    mapper.setInputData(image);
    const sampleDistance = 0.7 * Math.sqrt(image.getSpacing().map((v) => v * v).reduce((a, b) => a + b, 0));
    mapper.setSampleDistance(sampleDistance);

    const actor = vtkVolume.newInstance();
    actor.setMapper(mapper);
    actor.getProperty().setRGBTransferFunction(0, lookupTable);
    actor.getProperty().setScalarOpacity(0, piecewiseFunction);
    actor.getProperty().setInterpolationTypeToLinear();
    actor.getProperty().setScalarOpacityUnitDistance(
      0,
      vtkBoundingBox.getDiagonalLength(image.getBounds()) / Math.max(...image.getDimensions())
    );
    actor.getProperty().setGradientOpacityMinimumValue(0, 0);
    const dataArray = image.getPointData().getScalars() || image.getPointData().getArrays()[0];
    const dataRange = dataArray.getRange();
    // console.log(image.getBounds(), image.getDimensions(), image.getSpacing());
    actor.getProperty().setGradientOpacityMaximumValue(0, (dataRange[1] - dataRange[0]) * 0.05);
    // - Use shading based on gradient
    actor.getProperty().setShade(true);
    actor.getProperty().setUseGradientOpacity(0, true);
    // - generic good default
    actor.getProperty().setGradientOpacityMinimumOpacity(0, 0.0);
    actor.getProperty().setGradientOpacityMaximumOpacity(0, 1.0);
    actor.getProperty().setAmbient(0.2);
    actor.getProperty().setDiffuse(0.7);
    actor.getProperty().setSpecular(0.3);
    actor.getProperty().setSpecularPower(8.0);
    view3D.renderer.addVolume(actor);
    view3D.image = image;
    view3D.volumeMapper = mapper;
    view3D.volumeActor = actor;

    // Create image outline in 3D view
    const outline = vtkOutlineFilter.newInstance();
    outline.setInputData(image);
    const outlineMapper = vtkMapper.newInstance();
    outlineMapper.setInputData(outline.getOutputData());
    const outlineActor = vtkActor.newInstance();
    outlineActor.setMapper(outlineMapper);
    view3D.renderer.addActor(outlineActor);
    view3D.outline = outline;
    view3D.outlineMapper = outlineMapper;
    view3D.outlineActor = outlineActor;

    viewAttributes.forEach((obj, i) => {
        obj.reslice.setInputData(image);
        obj.renderer.addActor(obj.resliceActor);
        view3D.renderer.addActor(obj.resliceActor);
        obj.sphereSources.forEach((sphere) => {
            sphere.setRadius(arrayMax(image.getBounds()) / 36.0);
        });
        obj.sphereActors.forEach((actor) => {
            obj.renderer.addActor(actor);
            view3D.renderer.addActor(actor);
        });
        const reslice = obj.reslice;
        const viewType = xyzToViewType[i];

        // No need to update plane nor refresh when interaction
        // is on current view. Plane can't be changed with interaction on current
        // view. Refreshs happen automatically with `animation`.
        // Note: Need to refresh also the current view because of adding the mouse wheel
        // to change slicer
        viewAttributes.forEach((v) => {
            // Interactions in other views may change current plane
            v.widgetInstance.onInteractionEvent(({computeFocalPointOffset, canUpdateFocalPoint}) => {
                    // computeFocalPointOffset: Boolean which defines if the offset between focal point and
                    // reslice cursor display center has to be recomputed (while translation is applied)
                    // canUpdateFocalPoint: Boolean which defines if the focal point can be updated because
                    // the current interaction is a rotation
                    const activeViewType = widget.getWidgetState().getActiveViewType();
                    const keepFocalPointPosition = activeViewType !== viewType && canUpdateFocalPoint;
                    updateReslice({
                        viewType,
                        reslice,
                        actor: obj.resliceActor,
                        renderer: obj.renderer,
                        resetFocalPoint: false,
                        keepFocalPointPosition,
                        computeFocalPointOffset,
                        sphereSources: obj.sphereSources,
                    });
                }
            );
        });

        updateReslice({
            viewType,
            reslice,
            actor: obj.resliceActor,
            renderer: obj.renderer,
            resetFocalPoint: true, // At first initilization, center the focal point to the image center
            keepFocalPointPosition: false, // Don't update the focal point as we already set it to the center of the image
            computeFocalPointOffset: true, // Allow to compute the current offset between display reslice center and display focal point
            sphereSources: obj.sphereSources,
        });
        obj.interactor.render();
    });

    view3D.renderer.resetCamera();
    view3D.renderer.resetCameraClippingRange();

    // set max number of slices to slider.
    const maxNumberOfSlices = vec3.length(image.getDimensions());
    document.getElementById('slabNumber').max = maxNumberOfSlices;
}

// eslint-disable-next-line no-unused-vars
function load_data() {
    start_loading();
    const reader = vtkHttpDataSetReader.newInstance({fetchGzip: true});
    reader.setProgressCallback(
        (progressEvent) => {
            if (progressEvent.lengthComputable) {
                const percent = Math.floor(100 * progressEvent.loaded / progressEvent.total);
                loading_text.value = `Loading ... ${percent}%`;
            }
        }
    );
    reader.setUrl('https://kitware.github.io/vtk-js/data/volume/LIDC2.vti').then(() => {
        reader.loadData().then(() => {
            update_data(reader.getOutputData(), lookupTable1, piecewiseFunction1);
            stop_loading();
        });
    });
}

let flag_load_file_again = false;

function update_file(data) {
    const reader = vtkXMLImageDataReader.newInstance();
    reader.parseAsArrayBuffer(data);
    if (flag_load_file_again) {
        delete_context();
        create_context();
    }
    update_data(reader.getOutputData(), lookupTable2, piecewiseFunction2);
    flag_load_file_again = true;
}

function load_file(event) {
    event.preventDefault();
    const dataTransfer = event.dataTransfer;
    const files = event.target.files || dataTransfer.files;

    if (files.length === 1) {
        filename.value = files[0].name;
        start_loading();
        const fileReader = new FileReader();
        fileReader.onload = function onLoad() {
            if (filename.value.endsWith('.vti')) {
                update_file(fileReader.result);
                stop_loading();
            } else {
                bridge.receive_data(filename.value + ',' + fileReader.result, (msg) => {
                    const textEncoder = new TextEncoder();
                    update_file(textEncoder.encode(msg));
                    stop_loading();
                });
            }
        };
        fileReader.onprogress = function onProgress(e) {
            if (e.lengthComputable) {
                const percent = Math.floor(100 * e.loaded / e.total);
                loading_text.value = `Loading ... ${percent}%`;
            }
        };
        if (filename.value.endsWith('.vti')) {
            fileReader.readAsArrayBuffer(files[0]);
        } else {
            fileReader.readAsDataURL(files[0]);
        }
    }
}

function start_loading() {
    if(loading === null) {
        loading_text.value = 'Loading ...';
        const container = document.querySelector('.render');
        loading = ElLoading.service({
              target: container,
              lock: true,
              text: loading_text,
              background: 'rgba(0, 0, 0, 0.7)',
        });
    }
}

function stop_loading() {
  if(loading !== null) {
    loading.close();
    loading = null;
  }
}

function delete_obj(obj) {
    obj.orientationWidget.delete();
    obj.orientationAxes.delete();
    obj.sphereActors.forEach((actor) => {
        actor.delete();
    });
    obj.sphereMappers.forEach((mapper) => {
        mapper.delete();
    });
    obj.sphereSources.forEach((source) => {
        source.delete();
    });
    obj.resliceActor.delete();
    obj.resliceMapper.delete();
    obj.reslice.delete();
    // obj.widgetInstance.delete();
    // obj.widgetManager.removeWidgets();
    obj.widgetManager.delete();
    // obj.GLWindow.delete();
    obj.renderer.removeAllActors();
    obj.renderer.removeAllVolumes();
    obj.renderer.delete();
    obj.renderWindow.removeRenderer(obj.renderer);
    obj.renderWindow.removeView(obj.GLWindow);
    obj.renderWindow.render();
    obj.renderWindow.delete();
    obj.grw.setContainer(null);
    obj.grw.delete();
    obj.interactor.delete();
}

function delete_context() {
    if (context.value) {
        const { widget, widgetState, viewAttributes, view3D } = context.value;

        remove_event_listeners();

        viewAttributes.forEach((obj) => {
            delete_obj(obj);
        });

        delete_obj(view3D);
        view3D.image.delete();
        view3D.volumeMapper.delete();
        view3D.volumeActor.delete();
        view3D.outline.delete();
        view3D.outlineMapper.delete();
        view3D.outlineActor.delete();

        widget.delete();
        widgetState.unbindAll()
        widgetState.delete();

        context.value = null;
    }
}

onMounted(() => {
    create_context();
    create_bridge();
    // load_data();
});

onBeforeUnmount(() => {
    delete_bridge();
    delete_context();
});

</script>

<style scoped>
.con {
    display: flex;
    height: 100vh;
    width: 100vw;
}
.config {
    width: 320px;
}
.render {
    display: flex;
    width: calc(100vw - 320px);
    flex-wrap: wrap;
    justify-content: center;
}
.view {
    display: flex;
    height: 50%;
    width: 50%;
}
table {
    width: 100%;
    //border: 1px solid black;
}
.label {
    display: inline-block;
    width: 105px;
    overflow: hidden;
    text-overflow: ellipsis;
}
</style>