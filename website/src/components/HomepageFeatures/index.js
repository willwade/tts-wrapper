import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'Unified Interface',
    description: (
      <>
        One consistent API for multiple TTS services. Switch between engines with minimal code changes.
      </>
    ),
  },
  {
    title: 'Rich Feature Set',
    description: (
      <>
        SSML support, streaming capabilities, word-level timing, and advanced audio control across all supported engines.
      </>
    ),
  },
  {
    title: 'Extensive Engine Support',
    description: (
      <>
        Support for major cloud providers (AWS Polly, Google Cloud, Azure) and local engines (eSpeak, SAPI, AVSynth).
      </>
    ),
  },
  {
    title: 'Cross-Platform',
    description: (
      <>
        Works seamlessly on Windows, macOS, and Linux, with platform-specific optimizations.
      </>
    ),
  },
  {
    title: 'Advanced Audio Control',
    description: (
      <>
        Pause, resume, and stop functionality. Real-time audio streaming and playback control.
      </>
    ),
  },
  {
    title: 'Developer Friendly',
    description: (
      <>
        Comprehensive documentation, type hints, and examples make integration straightforward.
      </>
    ),
  },
];

function Feature({title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
} 