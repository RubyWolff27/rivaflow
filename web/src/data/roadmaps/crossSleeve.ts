import type { Roadmap } from '../../types/roadmap';

/**
 * The cross-sleeve roadmap — Ruby's own work, NOT the AJJ syllabus.
 *
 * This file exists precisely so the cross sleeve never enters
 * `curriculum_slot`. The Purple Belt page must stay byte-true to the Academy's
 * 2024 syllabus, because coaches sign off against their own document and an
 * extra requirement sitting in the guard block would read as one of theirs.
 * Nothing here is a belt requirement. Nothing here reaches the coach export.
 *
 * Structure follows the generic BJJ pedagogical spine (entries -> sweeps ->
 * back takes -> submissions -> games), which is a method, not a protected
 * expression. Cue wording is paraphrased from Ruby's own purchased roadmap for
 * his personal use; the artwork and layout are not reproduced.
 *
 * REACTIONS ARE SPARSE ON PURPOSE. Only the branches the source material
 * actually justifies are marked as reactions — inventing "if they do X" edges
 * would be fabricating jiu-jitsu Ruby never learned. Everything else is an
 * honest menu until he adds the reads himself.
 */
export const crossSleeveRoadmap: Roadmap = {
  id: 'cross-sleeve',
  title: 'Cross Sleeve',
  subtitle: 'Master the entry. Dominate the position. Finish the fight.',
  provenance:
    'Your own system — not the AJJ syllabus, not part of any coach sign-off.',
  principles: [
    { label: 'Protect', detail: 'Win the head battle.' },
    { label: 'Identify', detail: 'Read the reaction.' },
    { label: 'Connect', detail: 'Never lose the cross sleeve.' },
    { label: 'Execute', detail: 'Chain your attacks.' },
  ],
  root: {
    id: 'root',
    kind: 'choice',
    label: 'Start here — where are you gripping from?',
    stage: 'entry',
    children: [
      {
        id: 'entry-knee-shield',
        kind: 'choice',
        label: 'Knee shield',
        stage: 'entry',
        children: [
          {
            id: 'r-knee-shield-posted',
            kind: 'reaction',
            label: 'If they post the near knee to flatten you',
            children: [
              {
                id: 'sweep-shin-to-shin',
                kind: 'choice',
                label: 'Shin to shin',
                stage: 'sweep',
                cues: ['Clear the posted knee', 'Enter underneath', 'Attack ashi garami'],
                children: [
                  {
                    id: 'sweep-ashi-garami',
                    kind: 'choice',
                    label: 'Ashi garami',
                    stage: 'sweep',
                    cues: ['Pull them forward', 'Secure the legs', 'Sweep or attack'],
                  },
                ],
              },
            ],
          },
          {
            id: 'r-knee-shield-narrow',
            kind: 'reaction',
            label: 'If their base is wide and heavy',
            children: [
              {
                id: 'sweep-scissor',
                kind: 'choice',
                label: 'Scissor sweep',
                stage: 'sweep',
                cues: ['Keep their base narrow', 'Chop the outside knee', 'Come up on top'],
              },
            ],
          },
        ],
      },
      {
        id: 'entry-dlr',
        kind: 'choice',
        label: 'De La Riva',
        stage: 'entry',
        cues: ['Off-balance first', 'Sit up around the leg', 'Attack the back'],
        children: [
          {
            id: 'back-classic',
            kind: 'choice',
            label: 'Classic back take',
            stage: 'back',
          },
          {
            id: 'back-berimbolo',
            kind: 'choice',
            label: 'Berimbolo back take',
            stage: 'back',
          },
          {
            id: 'sweep-deep-dlr',
            kind: 'choice',
            label: 'Deep DLR sweep',
            stage: 'sweep',
          },
        ],
      },
      {
        id: 'entry-sit-up',
        kind: 'choice',
        label: 'Sit-up guard',
        stage: 'entry',
        cues: ['Build around the leg', 'Keep the cross sleeve', 'Wrestle up'],
        children: [
          { id: 'sweep-sit-up', kind: 'choice', label: 'Sit-up sweep', stage: 'sweep' },
          { id: 'back-crab-ride', kind: 'choice', label: 'Crab ride entry', stage: 'back' },
        ],
      },
      {
        id: 'entry-half-guard',
        kind: 'choice',
        label: 'Half guard',
        stage: 'entry',
        children: [
          { id: 'sweep-roll', kind: 'choice', label: 'Roll sweep', stage: 'sweep' },
          { id: 'back-butterfly', kind: 'choice', label: 'Butterfly back take', stage: 'back' },
        ],
      },
      {
        id: 'entry-closed-guard',
        kind: 'choice',
        label: 'Closed guard',
        stage: 'entry',
        children: [
          {
            id: 'r-closed-arm-back',
            kind: 'reaction',
            label: 'If they pull the trapped arm back',
            children: [
              { id: 'sub-omoplata', kind: 'choice', label: 'Omoplata', stage: 'submission' },
              { id: 'sweep-omoplata', kind: 'choice', label: 'Omoplata sweep', stage: 'sweep' },
            ],
          },
          {
            id: 'r-closed-posture',
            kind: 'reaction',
            label: 'If they posture up and stack',
            children: [
              { id: 'sub-triangle', kind: 'choice', label: 'Triangle choke', stage: 'submission' },
              { id: 'sub-armbar', kind: 'choice', label: 'Armbar options', stage: 'submission' },
            ],
          },
        ],
      },
      {
        id: 'entry-butterfly',
        kind: 'choice',
        label: 'Butterfly',
        stage: 'entry',
        children: [
          { id: 'sweep-butterfly', kind: 'choice', label: 'Butterfly sweep', stage: 'sweep' },
        ],
      },
      {
        id: 'entry-x-guard',
        kind: 'choice',
        label: 'X guard',
        stage: 'entry',
      },
      {
        id: 'entry-lasso',
        kind: 'choice',
        label: 'Lasso guard',
        stage: 'entry',
      },
      {
        id: 'entry-standing',
        kind: 'choice',
        label: 'Standing / collar & sleeve',
        stage: 'entry',
      },
      {
        id: 'finish-line',
        kind: 'choice',
        label: 'Finish line — sharpen the system',
        stage: 'drill',
        cues: ['Off balance', 'Angles', 'Timing'],
        children: [
          { id: 'drill-cla', kind: 'choice', label: 'CLA games', stage: 'drill' },
          { id: 'drill-grips', kind: 'choice', label: 'Grip-fighting drills', stage: 'drill' },
          { id: 'drill-positional', kind: 'choice', label: 'Positional drilling', stage: 'drill' },
          { id: 'drill-situational', kind: 'choice', label: 'Situational sparring', stage: 'drill' },
        ],
      },
      {
        id: 'sub-shin-to-shin-triangle',
        kind: 'choice',
        label: 'Shin-to-shin triangle',
        stage: 'submission',
      },
    ],
  },
};

export const ROADMAPS: Roadmap[] = [crossSleeveRoadmap];
