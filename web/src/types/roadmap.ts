/**
 * Shapes for the interactive roadmaps.
 *
 * The one rule that makes a grappling map honest: a CHOICE is something you
 * decide, a REACTION is something they do that forces your hand. The UI must
 * never present the second as the first — you don't get to pick what your
 * opponent does, you recognise it and read off what already applies.
 *
 * Node vocabulary follows the BJJML / Graphling convention (bjjgraph.org),
 * where every node resolves toward a positive transition, a negative one, or a
 * finish. `stage` is the poster-style spine; `kind` is the interaction model.
 *
 * Roadmaps deliberately hold NO curriculum data of their own beyond `slotId`.
 * A roadmap is Ruby's own system; the AJJ syllabus is the Academy's. They are
 * joined by reference and never merged — see the module note in
 * `data/roadmaps/crossSleeve.ts`.
 */

export type RoadmapStage =
  | 'entry'
  | 'sweep'
  | 'back'
  | 'submission'
  | 'drill'
  | 'principle';

export type RoadmapNodeKind = 'choice' | 'reaction';

export interface RoadmapNode {
  id: string;
  kind: RoadmapNodeKind;
  label: string;
  /** The 2-4 word coaching cues that expand inline, poster-style. */
  cues?: string[];
  stage?: RoadmapStage;
  /**
   * A declared curriculum slot this node corresponds to, when one legitimately
   * exists. Null for everything that is Ruby's own work — which, for the cross
   * sleeve, is all of it.
   */
  slotId?: number;
  /** Glossary movement, for the link into MovementDetail. */
  movementId?: string;
  children?: RoadmapNode[];
}

export interface Roadmap {
  id: string;
  title: string;
  subtitle: string;
  /** Where this came from, shown in the footer. Never claims to be syllabus. */
  provenance: string;
  principles?: { label: string; detail: string }[];
  root: RoadmapNode;
}
