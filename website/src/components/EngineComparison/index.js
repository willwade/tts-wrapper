import React from 'react';
import styles from './styles.module.css';

const engines = [
  {
    name: 'AWS Polly',
    type: 'Cloud',
    ssml: true,
    streaming: true,
    wordTiming: true,
    neuralVoices: true,
    customVoices: false,
    freeUsage: false,
  },
  {
    name: 'Google Cloud',
    type: 'Cloud',
    ssml: true,
    streaming: true,
    wordTiming: true,
    neuralVoices: true,
    customVoices: true,
    freeUsage: false,
  },
  {
    name: 'Microsoft Azure',
    type: 'Cloud',
    ssml: true,
    streaming: true,
    wordTiming: true,
    neuralVoices: true,
    customVoices: true,
    freeUsage: false,
  },
  {
    name: 'IBM Watson',
    type: 'Cloud',
    ssml: true,
    streaming: true,
    wordTiming: true,
    neuralVoices: true,
    customVoices: false,
    freeUsage: false,
  },
  {
    name: 'ElevenLabs',
    type: 'Cloud',
    ssml: false,
    streaming: true,
    wordTiming: false,
    neuralVoices: true,
    customVoices: true,
    freeUsage: true,
  },
  {
    name: 'Play.HT',
    type: 'Cloud',
    ssml: false,
    streaming: true,
    wordTiming: false,
    neuralVoices: true,
    customVoices: true,
    freeUsage: true,
  },
  {
    name: 'eSpeak',
    type: 'Local',
    ssml: true,
    streaming: true,
    wordTiming: true,
    neuralVoices: false,
    customVoices: false,
    freeUsage: true,
  },
  {
    name: 'SAPI',
    type: 'Local',
    ssml: true,
    streaming: true,
    wordTiming: true,
    neuralVoices: false,
    customVoices: false,
    freeUsage: true,
  },
  {
    name: 'AVSynth',
    type: 'Local',
    ssml: true,
    streaming: true,
    wordTiming: true,
    neuralVoices: false,
    customVoices: false,
    freeUsage: true,
  },
];

function Check({value}) {
  return value ? '✓' : '✗';
}

export default function EngineComparison() {
  return (
    <section className={styles.comparison}>
      <div className="container">
        <h2 className="text--center">Engine Comparison</h2>
        <div className={styles.tableWrapper}>
          <table className={styles.featureTable}>
            <thead>
              <tr>
                <th>Engine</th>
                <th>Type</th>
                <th>SSML</th>
                <th>Streaming</th>
                <th>Word Timing</th>
                <th>Neural Voices</th>
                <th>Custom Voices</th>
                <th>Free Usage</th>
              </tr>
            </thead>
            <tbody>
              {engines.map((engine) => (
                <tr key={engine.name}>
                  <td>{engine.name}</td>
                  <td>{engine.type}</td>
                  <td><Check value={engine.ssml} /></td>
                  <td><Check value={engine.streaming} /></td>
                  <td><Check value={engine.wordTiming} /></td>
                  <td><Check value={engine.neuralVoices} /></td>
                  <td><Check value={engine.customVoices} /></td>
                  <td><Check value={engine.freeUsage} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
} 