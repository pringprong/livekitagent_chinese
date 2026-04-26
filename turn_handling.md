LiveKit docs › Agents framework › Turn handling options

---

# Turn handling options

> Reference documentation for turn handling options in LiveKit Agents.

## TurnHandlingOptions

The `turn_handling` parameter accepts a `TurnHandlingOptions` object (or plain object) that controls [turn detection](https://docs.livekit.io/agents/logic/turns.md), [endpointing](https://docs.livekit.io/agents/logic/turns.md#endpointing-configuration), [interruption](https://docs.livekit.io/agents/logic/turns.md#interruptions), and [preemptive generation](https://docs.livekit.io/agents/multimodality/audio.md#preemptive-generation) behavior in an agent session. Pass it to the [`AgentSession`](https://docs.livekit.io/agents/logic/sessions.md) constructor.

### Usage

The following example creates an `AgentSession` with turn detection set to VAD and custom endpointing and interruption handling settings:

**Python**:

```python
from livekit.agents import AgentSession, TurnHandlingOptions

session = AgentSession(
    turn_handling=TurnHandlingOptions(
        turn_detection="vad",
        endpointing={
            "mode": "fixed",
            "min_delay": 0.5,
            "max_delay": 3.0,
        },
        interruption={
            "mode": "adaptive",
            "min_duration": 0.5,
            "resume_false_interruption": True,
        },
        preemptive_generation={
            "preemptive_tts": True,
        },
    ),
    # ... other parameters
)

```

---

**Node.js**:

```typescript
const session = new voice.AgentSession({
    turnHandling: {
        turnDetection: 'vad',
        endpointing: {
            minDelay: 500,
            maxDelay: 3000,
        },
        interruption: {
            mode: 'adaptive',
            minDuration: 500,
            resumeFalseInterruption: true,
        },
        preemptiveGeneration: {
            preemptiveTts: true,
        },
    },
    // ... other parameters
});

```

### Parameters

The following parameters are available in the `TurnHandlingOptions` object (the `turn_handling` argument):

- **`turn_detection`** _(TurnDetectionMode | None)_ (optional): Strategy for deciding when the user has finished speaking.

**Options:**

- [`"stt"`](https://docs.livekit.io/agents/logic/turns.md#stt-endpointing) - Rely on speech-to-text end-of-utterance cues.
- [`"vad"`](https://docs.livekit.io/agents/logic/turns.md#vad-only) - Rely on Voice Activity Detection (VAD) start and stop cues.
- [`"realtime_llm"`](https://docs.livekit.io/agents/logic/turns.md#realtime-models) - Use server-side detection from a realtime LLM.
- [`"manual"`](https://docs.livekit.io/agents/logic/turns.md#manual) - Control turn boundaries explicitly.
- `TurnDetector` instance - Plug-in custom detector (for example, [`MultilingualModel()`](https://docs.livekit.io/agents/logic/turns/turn-detector.md#supported-languages)).
If this parameter is omitted, the session chooses the best available mode in priority order: `realtime_llm → vad → stt → manual` and automatically falls back to the next available mode if the necessary model is missing. See [Turns overview](https://docs.livekit.io/agents/logic/turns.md) for mode descriptions and fallback behavior.

- **`endpointing`** _(EndpointingOptions)_ (optional): Options for endpointing behavior. See [EndpointingOptions](#endpointingoptions) for details.

- **`interruption`** _(InterruptionOptions)_ (optional): Options for interruption handling. See [InterruptionOptions](#interruptionoptions) for details.

- **`preemptive_generation`** _(PreemptiveGenerationOptions)_ (optional): Options for [preemptive generation](https://docs.livekit.io/agents/multimodality/audio.md#preemptive-generation) behavior. See [PreemptiveGenerationOptions](#preemptivegenerationoptions) for details. In Node.js this parameter is called `preemptiveGeneration`.

## EndpointingOptions

Options for endpointing behavior, which determines timing thresholds for turn completion. With fixed endpointing (the default), the agent always uses the configured `min_delay` and `max_delay`.

For context and configuration in a session, see [Endpointing configuration](https://docs.livekit.io/agents/logic/turns.md#endpointing-configuration) in the turns overview.

### Dynamic endpointing

Available in:
- [ ] Node.js
- [x] Python

When you use dynamic endpointing, the agent adapts the delay within the `min_delay` and `max_delay` range based on session pause statistics. This can result in a more responsive turn-taking experience over time.

The following example enables dynamic endpointing. Pass it to the `turn_handling` parameter of `AgentSession`:

```python
turn_handling = {
    "endpointing": {
        "mode": "dynamic",
        "min_delay": 0.5,
        "max_delay": 3.0,
    },
}

```

### Usage

To use fixed endpointing, set `mode` to `"fixed"`. In Node.js, dynamic endpointing is not supported and `fixed` is the only option.

**Python**:

```python
turn_handling = {
    "endpointing": {
        "mode": "fixed",
        "min_delay": 0.5,
        "max_delay": 3.0,
    },
}

```

---

**Node.js**:

```typescript
const turnHandling = {
    endpointing: {
        mode: 'fixed',
        minDelay: 500,
        maxDelay: 3000,
    },
};

```

### Parameters

The following parameters are available in the `endpointing` options object `EndpointingOptions`:

- **`mode`** _(Literal['dynamic', 'fixed'])_ (optional) - Default: `fixed`: Endpointing timing behavior. The endpointing delay is the time the agent waits before terminating the users's turn.

- `"fixed"` - Use the configured `min_delay` and `max_delay` values to determine the endpointing delay.
- Available in:
- [ ] Node.js
- [x] Python

`"dynamic"` - Adapt the delay within the `min_delay` and `max_delay` range based on session pause statistics (exponential moving average of between-utterance and between-turn pauses). Suits most conversations.

- **`min_delay`** _(float)_ (optional) - Default: `0.5 seconds`: Minimum time (in seconds) to wait since the last detected speech to declare the user's turn to be complete.

With [dynamic endpointing](https://docs.livekit.io/reference/agents/turn-handling-options.md#dynamic-endpointing) (Python only), this is the lower bound. The agent might use a longer effective delay when session pause statistics suggest slower turn-taking.

- In VAD mode, this effectively behaves like `max(VAD silence, min_delay)`.
- In STT mode, this is applied _after_ the STT end-of-speech signal, and therefore in addition to the STT provider's endpointing delay.

- **`max_delay`** _(float)_ (optional) - Default: `3.0 seconds`: Maximum time (in seconds) the agent waits before terminating the turn. This prevents the agent from waiting indefinitely for the user to continue speaking.

With [dynamic endpointing](https://docs.livekit.io/reference/agents/turn-handling-options.md#dynamic-endpointing) (Python only), this is the upper bound. The agent might use a shorter effective delay when session pause statistics suggest faster turn-taking.

> ℹ️ **Time units**
> 
> In Node.js, `min_delay` and `max_delay` are in milliseconds (for example, `500` and `3000`). Python uses seconds (for example, `0.5` and `3.0`).

## InterruptionOptions

Options for [interruption](https://docs.livekit.io/agents/logic/turns.md#interruptions) handling, including [adaptive](https://docs.livekit.io/agents/logic/turns/adaptive-interruption-handling.md) detection and [false interruption](https://docs.livekit.io/agents/logic/turns.md#false-interruptions) recovery.

### Usage

The following example creates turn handling options with adaptive interruption handling. Pass it to the `turn_handling` parameter of `AgentSession`:

**Python**:

```python
turn_handling = {
    "interruption": {
        "mode": "adaptive",
        "min_duration": 0.5,
        "min_words": 0,
        "discard_audio_if_uninterruptible": True,
        "false_interruption_timeout": 2.0,
        "resume_false_interruption": True,
    },
}

```

---

**Node.js**:

```typescript
const turnHandling = {
    interruption: {
        mode: 'adaptive',
        minDuration: 500,
        minWords: 0,
        discardAudioIfUninterruptible: true,
        falseInterruptionTimeout: 2000,
        resumeFalseInterruption: true,
    },
};

```

To disable interruptions entirely, set `enabled` to `false` in the interruption options:

**Python**:

```python
turn_handling = {
    "interruption": {"enabled": False},
}

```

---

**Node.js**:

```typescript
const turnHandling = {
    interruption: {
        enabled: false,
    },
};

```

### Parameters

The following parameters are available in the `interruption` options object `InterruptionOptions`:

- **`enabled`** _(bool)_ (optional) - Default: `True`: When `True`, the agent can be interrupted by user speech. When `False`, interruptions are disabled entirely. Use `{"enabled": False}` to disable; the previous bool shorthand is no longer supported.

- **`mode`** _(Literal['adaptive', 'vad'])_ (optional): Interruption detection strategy. Only applies when `enabled` is `True`.

**Options:**

- `"adaptive"`- Use context-aware interruption detection (barge-in model). To learn more, see [Adaptive interruption handling](https://docs.livekit.io/agents/logic/turns/adaptive-interruption-handling.md).
- `"vad"` - Use VAD for interruption detection. See [Interruption mode](https://docs.livekit.io/agents/logic/turns.md#interruption-mode) for when each mode applies.
If this parameter is omitted, the session uses `"adaptive"` when a turn detector model is configured with an STT that supports aligned transcripts. Otherwise, it falls back to `"vad"`.

- **`discard_audio_if_uninterruptible`** _(bool)_ (optional) - Default: `True`: When `True`, drop buffered audio while the agent is speaking and cannot be interrupted. This prevents audio buildup during uninterruptible speech. See [Interruptions](https://docs.livekit.io/agents/logic/turns.md#interruptions) for context.

- **`min_duration`** _(float)_ (optional) - Default: `0.5 seconds`: Minimum duration of speech to be considered as an interruption. Helps filter out brief sounds or noise that shouldn't trigger interruptions. Python uses seconds (for example, `0.5`); Node.js uses milliseconds (for example, `500`).

- **`min_words`** _(int)_ (optional) - Default: `0`: Minimum number of words to be considered as an interruption. Only used if STT is enabled. Set to a value greater than `0` to require actual speech content before triggering interruptions.

- **`false_interruption_timeout`** _(float | None)_ (optional) - Default: `2.0 seconds`: Amount of time (in seconds) to wait after an interruption before emitting an `agent_false_interruption` event if the user is silent and no user transcript is detected.

Set to `None` to disable false interruption detection. When disabled, all interruptions are treated as intentional. To learn more, see [False interruptions](https://docs.livekit.io/agents/logic/turns.md#false-interruptions). In Node.js, use milliseconds.

- **`resume_false_interruption`** _(bool)_ (optional) - Default: `True`: Whether to resume the agent's speech after a false interruption is detected. When `True`, the agent continues speaking from where it left off after the `false_interruption_timeout` period has passed with no user transcription. To learn more, see [False interruptions](https://docs.livekit.io/agents/logic/turns.md#false-interruptions).

## PreemptiveGenerationOptions

Options for [preemptive generation](https://docs.livekit.io/agents/multimodality/audio.md#preemptive-generation), which lets the agent begin generating a response before the user's end of turn is confirmed. By default, only the LLM runs preemptively — TTS starts once the turn is confirmed and the speech is scheduled. Deferring TTS reduces unnecessary compute when a user interrupts or when the transcript changes before the turn completes.

### Usage

The following example configures preemptive generation to also run TTS early and caps attempts for long utterances. Pass it to the `turn_handling` parameter of `AgentSession`:

**Python**:

```python
turn_handling = {
    "preemptive_generation": {
        "enabled": True,
        "preemptive_tts": True,
        "max_speech_duration": 10.0,
        "max_retries": 3,
    },
}

```

---

**Node.js**:

```typescript
const turnHandling = {
    preemptiveGeneration: {
        enabled: true,
        preemptiveTts: true,
        maxSpeechDuration: 10_000,
        maxRetries: 3,
    },
};

```

To disable preemptive generation entirely, set `enabled` to `false`:

**Python**:

```python
turn_handling = {
    "preemptive_generation": {"enabled": False},
}

```

---

**Node.js**:

```typescript
const turnHandling = {
    preemptiveGeneration: { enabled: false },
};

```

### Parameters

The following parameters are available in the `PreemptiveGenerationOptions` object.

**Python**:

- **`enabled`** _(bool)_ (optional) - Default: `True`: When `True`, preemptive generation is enabled. Set to `False` to disable preemptive generation entirely.

- **`preemptive_tts`** _(bool)_ (optional) - Default: `False`: Whether to also run TTS preemptively before the turn is confirmed. When `False`, only the LLM runs preemptively and TTS starts once the turn is confirmed and the speech is scheduled.

- **`max_speech_duration`** _(float)_ (optional) - Default: `10.0 seconds`: Maximum user speech duration (in seconds) for which preemptive generation is attempted. Beyond this threshold, preemptive generation is skipped since long utterances are more likely to change and users might expect slower responses.

- **`max_retries`** _(int)_ (optional) - Default: `3`: Maximum number of preemptive generation attempts per user turn. The counter resets when the turn completes.

---

**Node.js**:

- **`enabled`** _(boolean)_ (optional) - Default: `true`: When `true`, preemptive generation is enabled. Set to `false` to disable preemptive generation entirely.

- **`preemptiveTts`** _(boolean)_ (optional) - Default: `false`: Whether to also run TTS preemptively before the turn is confirmed. When `false`, only the LLM runs preemptively and TTS starts once the turn is confirmed and the speech is scheduled.

- **`maxSpeechDuration`** _(number)_ (optional) - Default: `10000 ms`: Maximum user speech duration (in milliseconds) for which preemptive generation is attempted. Beyond this threshold, preemptive generation is skipped since long utterances are more likely to change and users might expect slower responses.

- **`maxRetries`** _(number)_ (optional) - Default: `3`: Maximum number of preemptive generation attempts per user turn. The counter resets when the turn completes.

---

This document was rendered at 2026-04-25T01:53:18.005Z.
For the latest version of this document, see [https://docs.livekit.io/reference/agents/turn-handling-options.md](https://docs.livekit.io/reference/agents/turn-handling-options.md).

To explore all LiveKit documentation, see [llms.txt](https://docs.livekit.io/llms.txt).