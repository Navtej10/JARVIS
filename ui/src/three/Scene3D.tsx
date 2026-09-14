import React, { useEffect, useRef, useState } from "react";
import { Canvas, useThree, useFrame } from "@react-three/fiber";
import { bridgeClient, GestureEventMessage } from "../bridgeClient";
import * as THREE from "three";

function ManipulableBox({ id }: { id: string }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const baseScale = useRef<number>(1.0);
  const baseRotation = useRef<number>(0.0);
  const [scale, setScale] = useState<number>(1.0);
  const [rotation, setRotation] = useState<number>(0.0);

  const lastBounds = useRef<{x: number, y: number, width: number, height: number} | null>(null);

  useEffect(() => {
    return () => {
      bridgeClient.unregisterObject(id);
    };
  }, [id]);

  useFrame(({ camera }) => {
    if (!meshRef.current) return;
    
    const box3 = new THREE.Box3().setFromObject(meshRef.current);
    if (box3.isEmpty()) return;

    const corners = [
      new THREE.Vector3(box3.min.x, box3.min.y, box3.min.z),
      new THREE.Vector3(box3.min.x, box3.min.y, box3.max.z),
      new THREE.Vector3(box3.min.x, box3.max.y, box3.min.z),
      new THREE.Vector3(box3.min.x, box3.max.y, box3.max.z),
      new THREE.Vector3(box3.max.x, box3.min.y, box3.min.z),
      new THREE.Vector3(box3.max.x, box3.min.y, box3.max.z),
      new THREE.Vector3(box3.max.x, box3.max.y, box3.min.z),
      new THREE.Vector3(box3.max.x, box3.max.y, box3.max.z),
    ];
    
    let minX = Infinity, minY = Infinity;
    let maxX = -Infinity, maxY = -Infinity;
    
    corners.forEach(corner => {
      corner.project(camera);
      const px = ((corner.x + 1) / 2) * window.innerWidth;
      const py = (-(corner.y - 1) / 2) * window.innerHeight;
      minX = Math.min(minX, px);
      minY = Math.min(minY, py);
      maxX = Math.max(maxX, px);
      maxY = Math.max(maxY, py);
    });
    
    const bounds = {
      x: minX,
      y: minY,
      width: maxX - minX,
      height: maxY - minY
    };
    
    const last = lastBounds.current;
    if (!last || 
        Math.abs(last.x - bounds.x) > 2 || 
        Math.abs(last.y - bounds.y) > 2 || 
        Math.abs(last.width - bounds.width) > 2 || 
        Math.abs(last.height - bounds.height) > 2) {
      bridgeClient.registerObject(id, "3d_object", bounds, 10);
      lastBounds.current = bounds;
    }
  });

  useEffect(() => {
    const unsub = bridgeClient.onGestureEvent((msg: GestureEventMessage) => {
      if (msg.name === "two_hand_scale" && msg.target === id) {
        if (msg.state === "start") {
          baseScale.current = scale;
        } else if (msg.state === "hold") {
          const payload = (msg as any).payload;
          const factor = payload?.scale_factor || 1.0;
          setScale(baseScale.current * factor);
        } else if (msg.state === "release") {
          const payload = (msg as any).payload;
          const factor = payload?.scale_factor || 1.0;
          setScale(baseScale.current * factor);
          baseScale.current = scale;
        }
      } else if (msg.name === "rotate" && msg.target === id) {
        if (msg.state === "start") {
          baseRotation.current = rotation;
        } else if (msg.state === "hold") {
          const payload = (msg as any).payload;
          const delta = payload?.delta_angle || 0.0;
          setRotation(baseRotation.current + delta);
        } else if (msg.state === "release") {
          const payload = (msg as any).payload;
          const delta = payload?.delta_angle || 0.0;
          setRotation(baseRotation.current + delta);
          baseRotation.current = rotation;
        }
      }
    });
    return unsub;
  }, [id, scale, rotation]);

  return (
    <mesh ref={meshRef} scale={scale} rotation={[0, 0, rotation]}>
      <boxGeometry args={[2, 2, 2]} />
      <meshStandardMaterial color="orange" />
    </mesh>
  );
}

function CameraController() {
  const { camera } = useThree();
  const baseAngle = useRef(0);
  const [angle, setAngle] = useState(0);

  useEffect(() => {
    const unsub = bridgeClient.onGestureEvent((msg: GestureEventMessage) => {
      if (msg.name === "orbit_camera") {
        if (msg.state === "start") {
          baseAngle.current = angle;
        } else if (msg.state === "hold") {
          const payload = (msg as any).payload;
          const delta = payload?.delta_angle || 0;
          setAngle(baseAngle.current + delta);
        } else if (msg.state === "release") {
          const payload = (msg as any).payload;
          const delta = payload?.delta_angle || 0;
          setAngle(baseAngle.current + delta);
          baseAngle.current = angle;
        }
      }
    });
    return unsub;
  }, [angle]);

  useEffect(() => {
    // Spherical orbit: radius 10, y 5
    camera.position.x = 10 * Math.sin(angle);
    camera.position.z = 10 * Math.cos(angle);
    camera.position.y = 5;
    camera.lookAt(0, 0, 0);
  }, [angle, camera]);

  return null;
}

export function Scene3D() {
  return (
    <Canvas style={{ position: "absolute", inset: 0, pointerEvents: "none", zIndex: 10 }}>
      <CameraController />
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} intensity={1.0} />
      <ManipulableBox id="test-3d-box" />
    </Canvas>
  );
}
