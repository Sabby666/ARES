# ARES Visual Language & UX Architecture (Phase 17B)

## 1. Core Identity & Philosophy
ARES is an AI-powered autonomous web security assessment engine. The interface represents a high-end autonomous security intelligence console. It is precise, controlled, technical, and alive. 
It explicitly avoids generic admin templates, standard SOC card grids, and overly busy cyberpunk cliches. 

## 2. The Holographic Intelligence Core
The signature visual element of the product is the **ARES Core**, an interactive, multi-layered 3D abstraction built with React Three Fiber and Three.js. 

**3D Architecture:**
- **Central Nucleus:** The solid grounding core.
- **Inner Luminous Field:** A subtle energy field surrounding the core.
- **Orbital Rings:** Interlocking topological toruses representing data pathways.
- **Particle System:** Distributed nodes moving around the core.

**State Mapping:**
- `IDLE`: Slow breathing, minimal activity.
- `STARTING`: Rings activate, energy increases.
- `POLICY_CHECK`: Scanning sweeps, blue color theme.
- `RECON`: Nodes move outward, discovery signals travel, rapid rotation.
- `ANALYSIS`: Denser node activity, inner rings accelerate.
- `TOOL_EXECUTION`: Directional energy path, active warning (Amber) colors.
- `EVIDENCE`: Signals converge, blue color theme.
- `COMPLETED`: Calm stabilized state, green success hue.
- `BLOCKED`: Controlled contraction, muted violet.
- `ERROR`: Degraded state, red hue, minimal motion.

## 3. Color System
A refined, dark technology palette:
- **Environment:** Near-black (`#030508`) and deep navy-black (`#0A0E17`).
- **Primary Accent:** Electric Blue (`#2563EB`).
- **Secondary Accent:** Indigo/Violet (`#8B5CF6`).
- **Semantic States:**
  - SUCCESS: Restrained green (`#10B981`)
  - WARNING: Amber (`#F59E0B`)
  - BLOCKED: Violet (`#8B5CF6`)
  - ERROR: Crimson (`#EF4444`)
  - INFO: Blue (`#3B82F6`)

*Lighting Rule:* Restrained glow. Glow is limited to the Core, rings, active states, and specific navigation elements. 

## 4. Typography
Distinctive typographic system with strict hierarchy:
- **Display / Brand:** `Outfit` (Uppercase, strong tracking for titles).
- **UI / Body:** `Inter` (Clean, highly legible for reading).
- **Monospace:** `Fira Code` / `JetBrains Mono` (For timestamps, endpoints, IDs, technical telemetry).

## 5. Layout & Components
**Dashboard Layout:** Asymmetric composition anchored by the Core on the left, flanked by active intelligence flow and data streams. Generic KPI cards have been eliminated in favor of inline metric rails.
**Sidebar:** A minimal, elegant "Command Rail" using icons and quiet active states.
**Header:** Compact system header tracking environment (LOCAL MODE) and backend connectivity.
**Findings:** A split-pane analysis workspace (List + Details + Provenance) for high-density analysis.
**Agents Topology:** Represents agent relationships as a connected topology graph rather than independent cards.

## 6. Motion (Emil Kowalski Principles)
Motion is intentional, smooth, precise, and state-driven. GSAP is used for 3D tweening, while CSS powers snappy UI transitions (`cubic-bezier(0.16, 1, 0.3, 1)`).

## 7. Responsive Behavior & Accessibility
- **Responsive:** On smaller screens, the command rail collapses, right-side panels stack below the Core, and flows become scrollable. The Core scales down but is preserved.
- **Reduced Motion:** Fully supported. When enabled, 3D orbit speeds decrease, particle systems slow down, and CSS transitions bypass duration.

## 8. State Handling
- **Empty States:** The Core rests in IDLE state with "ARES CORE READY". The empty state remains visually rich.
- **Offline Backend:** The UI remains functional but shows a "LINK FAILED" status. The Core degrades to a safe idle state without faking data.
