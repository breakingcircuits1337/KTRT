"use client"

import { Canvas } from "@react-three/fiber"
import { OrbitControls, Float, Html, Environment } from "@react-three/drei"
import { useMemo } from "react"

type KnightStatus = "idle" | "active" | "complete" | "blocked"

type Knight = {
  id: string
  label: string
  role: string
  angle: number
  status: KnightStatus
}

const KNIGHTS: Knight[] = [
  { id: "research", label: "Bedivere", role: "Research", angle: 0, status: "complete" },
  { id: "evidence", label: "Percival", role: "Evidence", angle: Math.PI / 3, status: "complete" },
  { id: "planning", label: "Lancelot", role: "Planning", angle: (2 * Math.PI) / 3, status: "active" },
  { id: "debate", label: "Council", role: "Debate", angle: Math.PI, status: "idle" },
  { id: "judge", label: "Crown", role: "Judge", angle: (4 * Math.PI) / 3, status: "idle" },
  { id: "build", label: "Kay", role: "Build", angle: (5 * Math.PI) / 3, status: "idle" },
]

function statusClasses(status: KnightStatus) {
  switch (status) {
    case "active":
      return "border-amber-400/80 bg-amber-500/15 text-amber-200 shadow-[0_0_30px_rgba(251,191,36,0.28)]"
    case "complete":
      return "border-emerald-400/70 bg-emerald-500/10 text-emerald-200 shadow-[0_0_24px_rgba(52,211,153,0.18)]"
    case "blocked":
      return "border-rose-400/70 bg-rose-500/10 text-rose-200 shadow-[0_0_24px_rgba(251,113,133,0.18)]"
    default:
      return "border-zinc-700 bg-zinc-900/80 text-zinc-300"
  }
}

function RuneRing() {
  const runes = useMemo(() => Array.from({ length: 20 }), [])

  return (
    <group position={[0, 0.06, 0]}>
      {runes.map((_, i) => {
        const angle = (i / runes.length) * Math.PI * 2
        const radius = 4.55
        const x = Math.cos(angle) * radius
        const z = Math.sin(angle) * radius
        return (
          <Html key={i} position={[x, 0, z]} center transform distanceFactor={10}>
            <div className="select-none text-[10px] font-semibold tracking-[0.3em] text-cyan-200/55">
              ✦
            </div>
          </Html>
        )
      })}
    </group>
  )
}

function KnightSeat({ knight }: { knight: Knight }) {
  const radius = 6.2
  const x = Math.cos(knight.angle) * radius
  const z = Math.sin(knight.angle) * radius

  return (
    <group position={[x, 0.45, z]}>
      <mesh castShadow receiveShadow>
        <cylinderGeometry args={[0.7, 0.85, 0.35, 32]} />
        <meshStandardMaterial color={knight.status === "active" ? "#f59e0b" : knight.status === "complete" ? "#10b981" : "#27272a"} emissive={knight.status === "active" ? "#7c2d12" : knight.status === "complete" ? "#064e3b" : "#111111"} emissiveIntensity={knight.status === "idle" ? 0.15 : 1.2} />
      </mesh>

      <mesh position={[0, 0.68, 0]} castShadow>
        <sphereGeometry args={[0.34, 32, 32]} />
        <meshStandardMaterial color="#d4d4d8" metalness={0.85} roughness={0.18} emissive={knight.status === "active" ? "#f59e0b" : knight.status === "complete" ? "#10b981" : "#000000"} emissiveIntensity={knight.status === "idle" ? 0 : 0.8} />
      </mesh>

      <Html position={[0, 1.55, 0]} center distanceFactor={9}>
        <div className={`min-w-[120px] rounded-xl border px-3 py-2 text-center backdrop-blur-md ${statusClasses(knight.status)}`}>
          <div className="text-[11px] font-semibold uppercase tracking-[0.24em]">{knight.label}</div>
          <div className="mt-1 text-[10px] uppercase tracking-[0.2em] opacity-75">{knight.role}</div>
        </div>
      </Html>
    </group>
  )
}

function Excalibur() {
  return (
    <Float speed={1.2} rotationIntensity={0.1} floatIntensity={0.08}>
      <group position={[0, 3.7, 0]}>
        <mesh position={[0, 0.2, 0]} castShadow>
          <boxGeometry args={[0.12, 7.2, 0.22]} />
          <meshStandardMaterial color="#d4d4d8" metalness={1} roughness={0.15} emissive="#67e8f9" emissiveIntensity={0.18} />
        </mesh>

        <mesh position={[0, -3.15, 0]} castShadow>
          <boxGeometry args={[2.1, 0.16, 0.32]} />
          <meshStandardMaterial color="#f59e0b" metalness={0.9} roughness={0.22} emissive="#7c2d12" emissiveIntensity={0.6} />
        </mesh>

        <mesh position={[0, -3.55, 0]} castShadow>
          <cylinderGeometry args={[0.12, 0.12, 0.72, 24]} />
          <meshStandardMaterial color="#78350f" metalness={0.25} roughness={0.7} />
        </mesh>

        <mesh position={[0, -4.05, 0]} castShadow>
          <sphereGeometry args={[0.22, 24, 24]} />
          <meshStandardMaterial color="#fbbf24" metalness={0.95} roughness={0.18} emissive="#f59e0b" emissiveIntensity={0.8} />
        </mesh>
      </group>
    </Float>
  )
}

function PhilosopherStone() {
  return (
    <group position={[0, -0.25, 0]}>
      <mesh receiveShadow>
        <sphereGeometry args={[0.65, 48, 48]} />
        <meshStandardMaterial color="#22d3ee" emissive="#06b6d4" emissiveIntensity={1.8} roughness={0.08} metalness={0.15} />
      </mesh>
      <mesh position={[0, -0.04, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.85, 1.45, 48]} />
        <meshBasicMaterial color="#67e8f9" transparent opacity={0.45} />
      </mesh>
    </group>
  )
}

function RoundTable() {
  return (
    <group>
      <mesh receiveShadow castShadow position={[0, 0, 0]}>
        <cylinderGeometry args={[4.25, 4.55, 0.5, 64]} />
        <meshStandardMaterial color="#3f2b1d" roughness={0.9} metalness={0.08} />
      </mesh>

      <mesh receiveShadow castShadow position={[0, -0.4, 0]}>
        <cylinderGeometry args={[1.1, 1.4, 1.2, 32]} />
        <meshStandardMaterial color="#1c1917" roughness={0.92} metalness={0.15} />
      </mesh>

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.26, 0]}>
        <ringGeometry args={[2.1, 4.2, 64]} />
        <meshBasicMaterial color="#f59e0b" transparent opacity={0.24} />
      </mesh>
    </group>
  )
}

function DragonSilhouette() {
  return (
    <Html position={[0, 6.6, -5.6]} center distanceFactor={14}>
      <div className="rounded-full border border-cyan-400/20 bg-zinc-950/50 px-4 py-1 text-[10px] uppercase tracking-[0.35em] text-cyan-100/65 backdrop-blur-md">
        Dragon Guardian
      </div>
    </Html>
  )
}

function SceneContent() {
  return (
    <>
      <color attach="background" args={["#09090b"]} />
      <fog attach="fog" args={["#09090b", 13, 26]} />

      <ambientLight intensity={0.6} />
      <directionalLight position={[8, 10, 7]} intensity={2.1} castShadow shadow-mapSize-width={2048} shadow-mapSize-height={2048} />
      <pointLight position={[0, 2.2, 0]} intensity={28} color="#06b6d4" distance={8} />
      <pointLight position={[0, 7, 0]} intensity={14} color="#f59e0b" distance={12} />

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1, 0]} receiveShadow>
        <planeGeometry args={[28, 28]} />
        <meshStandardMaterial color="#09090b" roughness={1} metalness={0} />
      </mesh>

      <RoundTable />
      <RuneRing />
      <PhilosopherStone />
      <Excalibur />
      <DragonSilhouette />

      {KNIGHTS.map((knight) => (
        <KnightSeat key={knight.id} knight={knight} />
      ))}

      <Environment preset="night" />
      <OrbitControls enablePan={false} minDistance={8} maxDistance={15} minPolarAngle={0.7} maxPolarAngle={1.35} />
    </>
  )
}

export default function TKTRRoundTableScene() {
  return (
    <div className="relative h-[720px] w-full overflow-hidden rounded-[28px] border border-amber-500/20 bg-gradient-to-b from-zinc-950 via-zinc-950 to-black shadow-2xl">
      <div className="absolute inset-x-0 top-0 z-10 flex items-center justify-between border-b border-zinc-800/80 bg-black/30 px-6 py-4 backdrop-blur-md">
        <div>
          <div className="text-xs uppercase tracking-[0.4em] text-cyan-200/75">TKTR 2026</div>
          <div className="mt-1 text-lg font-semibold text-amber-100">The Knights of Merlin</div>
        </div>
        <div className="rounded-full border border-amber-500/20 bg-amber-400/10 px-4 py-2 text-xs uppercase tracking-[0.3em] text-amber-200">
          Planning Active
        </div>
      </div>

      <Canvas camera={{ position: [0, 8.5, 10.5], fov: 42 }} shadows>
        <SceneContent />
      </Canvas>

      <div className="absolute bottom-4 left-4 right-4 z-10 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <div className="rounded-2xl border border-zinc-800/80 bg-black/45 p-4 backdrop-blur-md">
          <div className="text-[11px] uppercase tracking-[0.28em] text-zinc-400">Quest</div>
          <div className="mt-2 text-sm text-zinc-100">Build an MCP-backed research lab with debate, judge, and forge phases.</div>
        </div>
        <div className="rounded-2xl border border-zinc-800/80 bg-black/45 p-4 backdrop-blur-md">
          <div className="text-[11px] uppercase tracking-[0.28em] text-zinc-400">Alchemy Stage</div>
          <div className="mt-2 text-sm text-amber-200">Dissolution / Planning</div>
        </div>
        <div className="rounded-2xl border border-zinc-800/80 bg-black/45 p-4 backdrop-blur-md">
          <div className="text-[11px] uppercase tracking-[0.28em] text-zinc-400">Judge Gate</div>
          <div className="mt-2 text-sm text-zinc-100">Pending after Council debate</div>
        </div>
        <div className="rounded-2xl border border-zinc-800/80 bg-black/45 p-4 backdrop-blur-md">
          <div className="text-[11px] uppercase tracking-[0.28em] text-zinc-400">Stone Integrity</div>
          <div className="mt-2 text-sm text-cyan-200">87% projected confidence</div>
        </div>
      </div>
    </div>
  )
}
