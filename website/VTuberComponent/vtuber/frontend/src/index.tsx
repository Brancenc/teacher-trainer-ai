import { Streamlit, RenderData } from "streamlit-component-lib"
import {Engine,Matrix,Color4,AbstractMesh,AnimationPropertiesOverride, SceneLoader,Bone,BoneLookController, FreeCamera,Scene,Texture, HemisphericLight, Vector3, MeshBuilder,PBRMaterial, StandardMaterial} from "@babylonjs/core";
import "@babylonjs/loaders/glTF";
import { env } from "process";
// Add text and a button to the DOM. (You could also add these directly
// to index.html.)
const span = document.body.appendChild(document.createElement("span"))
//const info = span.appendChild(document.createElement("p"));
const renderCanvas = span.appendChild(document.createElement("canvas"))

renderCanvas.width = 200;
renderCanvas.height = 200;
renderCanvas.style.borderRadius ="15px";
renderCanvas.style.boxShadow = "0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19)";
renderCanvas.style.backgroundImage = "url('ClassroomBackground.png')";
renderCanvas.style.backgroundSize = "400px 200px";

let lookPos = new Vector3(0,3,3);
let mousePos = new Vector3(0,3,3);


let mouthMesh : AbstractMesh|null = null;
let lEyeMesh : AbstractMesh|null = null;
let rEyeMesh : AbstractMesh|null = null;

let eyePositions: {[key:string]:number[]} = {
	"Neutral":[0,0],
	"Angry":[0,0.125],
	"Sad":[0,0.25],
	"Surprised":[0.25,0.125],
}
let mouthPositions: {[key:string]:number[]} = {
	"A":[0,0],
	"O":[0.25,0],
	"C":[0.5,0],
	"G":[0.75,0],
	"L":[0.0,0.125],
	"B":[0.25,0.125],
	"F":[0.5,0.125],
	"Ee":[0.75,0.125],
	"TH":[0.0,0.25],
	"CH":[0.25,0.25],
	"U":[0.5,0.25],
	"Q":[0.75,0.25],
	"Rest":[0.0,0.375],
	"Rest2":[0.25,0.375],
	"Frown":[0.5,0.375],
	"BigFrown":[0.75,0.375],
	"Judging":[0.0,0.5],
	"BigSmile":[0.25,0.5],
}

const engine = new Engine(renderCanvas, true); // Generate the BABYLON 3D engine
const createScene = function () {
	// Creates a basic Babylon Scene object
	const scene = new Scene(engine);
	scene.clearColor = new Color4(0,0,0,0);
    scene.animationPropertiesOverride = new AnimationPropertiesOverride();
    scene.animationPropertiesOverride.enableBlending = true;
	scene.animationPropertiesOverride.blendingSpeed = 0.2;
	// Creates and positions a free camera
	const camera = new FreeCamera("camera1", 
		new Vector3(0, 3, 3), scene);
	// Targets the camera to scene origin
	camera.setTarget(new Vector3(0,3,0));
	// This attaches the camera to the canvas
	//camera.attachControl(renderCanvas, true);
	// Creates a light, aiming 0,1,0 - to the sky
	const light = new HemisphericLight("light", 
		new Vector3(0, 1, 0), scene);
	// Dim the light a small amount - 0 to 1
	light.intensity = 0.7;
	//const sphere = MeshBuilder.CreateSphere("sphere", { diameter: 2});
	// Move the sphere upward 1/2 its height
	SceneLoader.ImportMeshAsync("","","SecondGrader.glb").then(
	(result)=>{
		var skl = result.meshes[1].skeleton;
		
		let headBone = skl?.bones.find((b:Bone)=>{return b.name == "Head";}) as Bone;

		let bCtnlr = new BoneLookController( result.meshes[1], headBone, lookPos,
			{ adjustYaw: Math.PI * 1.0, adjustPitch: Math.PI * 1.0, adjustRoll: Math.PI * 0.0 });
		scene.registerBeforeRender(function () {
			const newLookPos = Vector3.Lerp(lookPos,mousePos,0.2);
			lookPos.x = newLookPos.x;
			lookPos.y = newLookPos.y;
			lookPos.z = newLookPos.z;
			bCtnlr.update();
		  });	
		var mat = new PBRMaterial("myMat", scene);
		mat.needDepthPrePass = true
		mat.metallic = 0.1;
		mat.roughness = 1;
		var tex = new Texture("skaterMaleA.png",scene,false,false);
		mat.albedoTexture = tex;

		result.meshes[1].material = mat;

		((result.meshes[3].material as PBRMaterial).albedoTexture as Texture).vOffset = 0.375;
		mouthMesh = result.meshes[3];

		((result.meshes[2].material as PBRMaterial).albedoTexture as Texture).uOffset = 0.0;
		((result.meshes[2].material as PBRMaterial).albedoTexture as Texture).vOffset = 0.125;
		lEyeMesh = result.meshes[2];

		((result.meshes[4].material as PBRMaterial).albedoTexture as Texture).uOffset = 0.0;
		((result.meshes[4].material as PBRMaterial).albedoTexture as Texture).vOffset = 0.125;
		rEyeMesh = result.meshes[4];
		scene.animationGroups[0].stop();
	});
	
	// Built-in 'ground' shape.
	const ground = MeshBuilder.CreateGround("ground", 
		{width: 6, height: 6}, scene);
		
	var mouseMove = function(evt:MouseEvent){
		evt.preventDefault();

		//console.log("Mouse X:", scene.pointerX);
		//console.log("Mouse Y:", scene.pointerY);
		const rect = renderCanvas.getBoundingClientRect();
		let xPos = evt.clientX - rect.left;
		let yPos = evt.clientY - rect.top;


		let worldPos = Vector3.Unproject(new Vector3(xPos,yPos,-0.99),engine.getRenderWidth(),
		engine.getRenderHeight(),
			Matrix.Identity(),scene.getViewMatrix(),
		scene.getProjectionMatrix());

		//info.textContent = "Mouse X:" + xPos + "MouseY:" + yPos + "PtrX:" + scene.pointerX + "PtrY:" + scene.pointerY;
		mousePos.x = worldPos.x;
		mousePos.y = worldPos.y;
		mousePos.z = worldPos.z;
		//sphere.position = lookPos;
		//info.textContent = "Mouse X:" + scene.pointerX + "\nMouseY:" + scene.pointerY;
	}

	window.addEventListener('mousemove',mouseMove,true);

	return scene;
};

const scene = createScene(); //Call the createScene function
// Register a render loop to repeatedly render the scene

engine.runRenderLoop(function () {
		scene.render();
});
/*scene.onPointerObservable.add((eventData) => {
	console.log("Mouse X:", scene.pointerX);
	console.log("Mouse Y:", scene.pointerY);
});*/
// Watch for browser/canvas resize events
window.addEventListener("resize", function () {
		engine.resize();
});
// Add a click handler to our button. It will send data back to Streamlit.
let isFocused = false

renderCanvas.onfocus = function(): void {
  isFocused = true
}

renderCanvas.onblur = function(): void {
  isFocused = false
}

/**
 * The component's render function. This will be called immediately after
 * the component is initially loaded, and then again every time the
 * component gets new data from Python.
 */
function onRender(event: Event): void {
  // Get the RenderData from the event
  const data = (event as CustomEvent<RenderData>).detail

  // Maintain compatibility with older versions of Streamlit that don't send
  // a theme object.
  if (data.theme) {
    // Use CSS vars to style our button border. Alternatively, the theme style
    // is defined in the data.theme object.
    const borderStyling = `1px solid var(${
      isFocused ? "--primary-color" : "gray"
    })`
    renderCanvas.style.border = borderStyling
    renderCanvas.style.outline = borderStyling
  }

  // RenderData.args is the JSON dictionary of arguments sent from the
  // Python script.
  //let camX = data.args["camX"]
  let animName = data.args["animName"]
  //scene.animationGroups[animName].play()
  scene.stopAllAnimations();
  
  let aGroup = scene.getAnimationGroupByName(animName)
  /*
  Angry
  Disgust
  Happy
  Idling
  Sad
  Surpised
  Terrified
  */
  if( animName == "Angry"){
	((lEyeMesh?.material as PBRMaterial).albedoTexture as Texture).uOffset = eyePositions["Angry"][0];
	((lEyeMesh?.material as PBRMaterial).albedoTexture as Texture).vOffset = eyePositions["Angry"][1];

	((rEyeMesh?.material as PBRMaterial).albedoTexture as Texture).uOffset = eyePositions["Angry"][0];
	((rEyeMesh?.material as PBRMaterial).albedoTexture as Texture).vOffset = eyePositions["Angry"][1];

	((mouthMesh?.material as PBRMaterial).albedoTexture as Texture).uOffset = mouthPositions["Judging"][0];
	((mouthMesh?.material as PBRMaterial).albedoTexture as Texture).vOffset = mouthPositions["Judging"][1];
  }
  if( animName == "Disgust"){
	((lEyeMesh?.material as PBRMaterial).albedoTexture as Texture).uOffset = eyePositions["Surprised"][0];
	((lEyeMesh?.material as PBRMaterial).albedoTexture as Texture).vOffset = eyePositions["Surprised"][1];

	((rEyeMesh?.material as PBRMaterial).albedoTexture as Texture).uOffset = eyePositions["Surprised"][0];
	((rEyeMesh?.material as PBRMaterial).albedoTexture as Texture).vOffset = eyePositions["Surprised"][1];

	((mouthMesh?.material as PBRMaterial).albedoTexture as Texture).uOffset = mouthPositions["BigFrown"][0];
	((mouthMesh?.material as PBRMaterial).albedoTexture as Texture).vOffset = mouthPositions["BigFrown"][1];
  }
  if( animName == "Happy"){
	((lEyeMesh?.material as PBRMaterial).albedoTexture as Texture).uOffset = eyePositions["Neutral"][0];
	((lEyeMesh?.material as PBRMaterial).albedoTexture as Texture).vOffset = eyePositions["Neutral"][1];

	((rEyeMesh?.material as PBRMaterial).albedoTexture as Texture).uOffset = eyePositions["Neutral"][0];
	((rEyeMesh?.material as PBRMaterial).albedoTexture as Texture).vOffset = eyePositions["Neutral"][1];

	((mouthMesh?.material as PBRMaterial).albedoTexture as Texture).uOffset = mouthPositions["BigSmile"][0];
	((mouthMesh?.material as PBRMaterial).albedoTexture as Texture).vOffset = mouthPositions["BigSmile"][1];
  }
  if( animName == "Idling"){
	((lEyeMesh?.material as PBRMaterial).albedoTexture as Texture).uOffset = eyePositions["Neutral"][0];
	((lEyeMesh?.material as PBRMaterial).albedoTexture as Texture).vOffset = eyePositions["Neutral"][1];

	((rEyeMesh?.material as PBRMaterial).albedoTexture as Texture).uOffset = eyePositions["Neutral"][0];
	((rEyeMesh?.material as PBRMaterial).albedoTexture as Texture).vOffset = eyePositions["Neutral"][1];

	((mouthMesh?.material as PBRMaterial).albedoTexture as Texture).uOffset = mouthPositions["Rest"][0];
	((mouthMesh?.material as PBRMaterial).albedoTexture as Texture).vOffset = mouthPositions["Rest"][1];
  }
  if( animName == "Sad"){
	((lEyeMesh?.material as PBRMaterial).albedoTexture as Texture).uOffset = eyePositions["Sad"][0];
	((lEyeMesh?.material as PBRMaterial).albedoTexture as Texture).vOffset = eyePositions["Sad"][1];

	((rEyeMesh?.material as PBRMaterial).albedoTexture as Texture).uOffset = eyePositions["Sad"][0];
	((rEyeMesh?.material as PBRMaterial).albedoTexture as Texture).vOffset = eyePositions["Sad"][1];

	((mouthMesh?.material as PBRMaterial).albedoTexture as Texture).uOffset = mouthPositions["Frown"][0];
	((mouthMesh?.material as PBRMaterial).albedoTexture as Texture).vOffset = mouthPositions["Frown"][1];
  }
  if( animName == "Surprised"){
	((lEyeMesh?.material as PBRMaterial).albedoTexture as Texture).uOffset = eyePositions["Surprised"][0];
	((lEyeMesh?.material as PBRMaterial).albedoTexture as Texture).vOffset = eyePositions["Surprised"][1];

	((rEyeMesh?.material as PBRMaterial).albedoTexture as Texture).uOffset = eyePositions["Surprised"][0];
	((rEyeMesh?.material as PBRMaterial).albedoTexture as Texture).vOffset = eyePositions["Surprised"][1];

	((mouthMesh?.material as PBRMaterial).albedoTexture as Texture).uOffset = mouthPositions["Rest2"][0];
	((mouthMesh?.material as PBRMaterial).albedoTexture as Texture).vOffset = mouthPositions["Rest2"][1];
  }
  aGroup?.start(true, 1.0, aGroup.from, aGroup.to, false)
  // We tell Streamlit to update our frameHeight after each render event, in
  // case it has changed. (This isn't strictly necessary for the example
  // because our height stays fixed, but this is a low-cost function, so
  // there's no harm in doing it redundantly.)
  Streamlit.setFrameHeight()
}

// Attach our `onRender` handler to Streamlit's render event.
Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender)

// Tell Streamlit we're ready to start receiving data. We won't get our
// first RENDER_EVENT until we call this function.
Streamlit.setComponentReady()

// Finally, tell Streamlit to update our initial height. We omit the
// `height` parameter here to have it default to our scrollHeight.
Streamlit.setFrameHeight()
