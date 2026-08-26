import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { Box, Info, X } from 'lucide-react';
import { Location, RiskScore } from '../types';

interface DigitalTwinViewProps {
  locations: Location[];
  riskScores: RiskScore[];
}

export const DigitalTwinView: React.FC<DigitalTwinViewProps> = ({ locations, riskScores }) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const [inspectedLocation, setInspectedLocation] = useState<Location | null>(locations[0] || null);

  useEffect(() => {
    if (!mountRef.current) return;

    const container = mountRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight || 520;

    // 1. Scene Setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x070b14);
    scene.fog = new THREE.FogExp2(0x070b14, 0.025);

    // 2. Camera Setup
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(24, 20, 28);
    camera.lookAt(0, 0, 0);

    // 3. Renderer Setup
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // 4. Lighting
    const ambientLight = new THREE.AmbientLight(0x334155, 1.8);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x38bdf8, 2.5);
    dirLight.position.set(20, 30, 15);
    dirLight.castShadow = true;
    scene.add(dirLight);

    const pointLight = new THREE.PointLight(0xf43f5e, 3, 25);
    pointLight.position.set(-6, 4, -6);
    scene.add(pointLight);

    // 5. Ground Grid Platform
    const gridHelper = new THREE.GridHelper(40, 40, 0x0ea5e9, 0x1e293b);
    gridHelper.position.y = -0.01;
    scene.add(gridHelper);

    // Interactive Meshes Array for Raycaster
    const interactiveMeshes: Array<{ mesh: THREE.Mesh; locationIndex: number }> = [];

    // BESS Building (Sector 1)
    const bessGeo = new THREE.BoxGeometry(7, 3, 5);
    const bessMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      roughness: 0.3,
      metalness: 0.8
    });
    const bessMesh = new THREE.Mesh(bessGeo, bessMat);
    bessMesh.position.set(-8, 1.5, -8);
    scene.add(bessMesh);
    interactiveMeshes.push({ mesh: bessMesh, locationIndex: 0 });

    // BESS Heat Hazard Halo
    const haloGeo = new THREE.CylinderGeometry(4.5, 4.5, 0.2, 32);
    const haloMat = new THREE.MeshBasicMaterial({
      color: 0xf43f5e,
      transparent: true,
      opacity: 0.35
    });
    const haloMesh = new THREE.Mesh(haloGeo, haloMat);
    haloMesh.position.set(-8, 0.1, -8);
    scene.add(haloMesh);

    // Solar Yard Arrays (Sector 2)
    for (let x = 4; x <= 12; x += 4) {
      for (let z = -10; z <= -4; z += 3) {
        const panelGeo = new THREE.BoxGeometry(2.5, 0.2, 1.8);
        const panelMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, metalness: 0.9, roughness: 0.1 });
        const panel = new THREE.Mesh(panelGeo, panelMat);
        panel.position.set(x, 1, z);
        panel.rotation.x = Math.PI / 8;
        scene.add(panel);
        interactiveMeshes.push({ mesh: panel, locationIndex: 1 });
      }
    }

    // Refinery Cracker Tower (Sector 3)
    const towerGeo = new THREE.CylinderGeometry(1.5, 2, 8, 24);
    const towerMat = new THREE.MeshStandardMaterial({ color: 0x475569, metalness: 0.7, roughness: 0.4 });
    const tower = new THREE.Mesh(towerGeo, towerMat);
    tower.position.set(-8, 4, 8);
    scene.add(tower);
    interactiveMeshes.push({ mesh: tower, locationIndex: 2 });

    // Rooftop HVAC Structure (Sector 4)
    const hvacGeo = new THREE.BoxGeometry(9, 4, 6);
    const hvacMat = new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.5, roughness: 0.5 });
    const hvac = new THREE.Mesh(hvacGeo, hvacMat);
    hvac.position.set(8, 2, 8);
    scene.add(hvac);
    interactiveMeshes.push({ mesh: hvac, locationIndex: 3 });

    // Animated Camera Frustums / Cones
    const createCamCone = (x: number, y: number, z: number, color: number) => {
      const coneGeo = new THREE.ConeGeometry(3, 7, 16, 1, true);
      const coneMat = new THREE.MeshBasicMaterial({
        color,
        wireframe: true,
        transparent: true,
        opacity: 0.35
      });
      const cone = new THREE.Mesh(coneGeo, coneMat);
      cone.position.set(x, y, z);
      cone.rotation.x = Math.PI;
      scene.add(cone);
    };

    createCamCone(-8, 6, -8, 0x06b6d4);
    createCamCone(8, 6, -7, 0x0ea5e9);
    createCamCone(-8, 8, 8, 0xf59e0b);

    // Raycaster for interactive click inspection
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const onPointerDown = (event: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const targetMeshes = interactiveMeshes.map(im => im.mesh);
      const intersects = raycaster.intersectObjects(targetMeshes);

      if (intersects.length > 0) {
        const hit = interactiveMeshes.find(im => im.mesh === intersects[0].object);
        if (hit && locations[hit.locationIndex]) {
          setInspectedLocation(locations[hit.locationIndex]);
        }
      }
    };

    renderer.domElement.addEventListener('click', onPointerDown);

    // Animation & Orbit Loop
    let angle = 0;
    let animId: number;

    const animate = () => {
      animId = requestAnimationFrame(animate);
      angle += 0.003;

      camera.position.x = 28 * Math.cos(angle);
      camera.position.z = 28 * Math.sin(angle);
      camera.lookAt(0, 1, 0);

      const scale = 1 + Math.sin(Date.now() * 0.004) * 0.08;
      haloMesh.scale.set(scale, 1, scale);

      renderer.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight || 520;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animId);
      renderer.domElement.removeEventListener('click', onPointerDown);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
    };
  }, [locations, riskScores]);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="glass-panel rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Box className="w-5 h-5 text-cyan-400" />
          <div>
            <h2 className="text-sm font-bold text-slate-200">
              FACILITY DIGITAL TWIN 3D SPATIAL OVERWATCH
            </h2>
            <span className="text-[11px] text-slate-400">
              Interactive Three.js WebGL model: click any structure to inspect real-time telemetry
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300">
            AUTO-ORBIT ACTIVE
          </span>
          <span className="px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-800 text-cyan-400">
            THREE.JS WEBGL 2.0
          </span>
        </div>
      </div>

      {/* 3D Viewport Container */}
      <div className="glass-panel rounded-xl p-4">
        <div
          ref={mountRef}
          className="w-full h-[520px] rounded-lg border border-slate-800 overflow-hidden relative cursor-pointer"
        >
          {/* Overlay Status */}
          <div className="absolute top-4 left-4 bg-slate-900/90 backdrop-blur-md p-3 rounded-lg border border-slate-800 text-xs font-mono space-y-1 z-10">
            <div className="text-cyan-400 font-bold">DIGITAL TWIN STATUS: SYNCHRONIZED</div>
            <div className="text-slate-300">SECTORS RENDERED: 4 ACTIVE</div>
            <div className="text-slate-300">THERMAL VOLUMETRIC HALOS: 1 ACTIVE</div>
            <div className="text-slate-300">CAMERA FOV CONES: 3 ACTIVE</div>
          </div>

          {/* Interactive Inspected Sector Drawer */}
          {inspectedLocation && (
            <div className="absolute top-4 right-4 bg-slate-900/95 backdrop-blur-md p-3.5 rounded-xl border border-slate-700 w-80 text-xs shadow-2xl z-20 space-y-2">
              <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                <div className="flex items-center gap-1.5">
                  <Info className="w-4 h-4 text-cyan-400" />
                  <span className="font-bold text-slate-100">{inspectedLocation.code}</span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setInspectedLocation(null);
                  }}
                  className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>

              <h4 className="font-bold text-slate-200 text-xs">{inspectedLocation.name}</h4>

              <div className="grid grid-cols-2 gap-1.5 bg-slate-950 p-2 rounded border border-slate-800 font-mono text-[11px]">
                <div>
                  <span className="text-slate-400 text-[10px] block">Temperature:</span>
                  <strong className="text-slate-100">{inspectedLocation.current_temp_c?.toFixed(1) || 26.5}°C</strong>
                </div>
                <div>
                  <span className="text-slate-400 text-[10px] block">Risk Score:</span>
                  <strong className="text-rose-400">{inspectedLocation.current_risk_score.toFixed(1)} / 100</strong>
                </div>
                <div>
                  <span className="text-slate-400 text-[10px] block">Baseline:</span>
                  <strong className="text-slate-300">{inspectedLocation.baseline_temp_c.toFixed(1)}°C</strong>
                </div>
                <div>
                  <span className="text-slate-400 text-[10px] block">Threshold:</span>
                  <strong className="text-amber-400">{inspectedLocation.risk_threshold}</strong>
                </div>
              </div>
            </div>
          )}

          <div className="absolute bottom-4 right-4 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-800 text-[11px] font-mono text-slate-400 z-10">
            Coordinate System: WGS84 Local Cartesian (Abu Dhabi Facility)
          </div>
        </div>
      </div>
    </div>
  );
};
