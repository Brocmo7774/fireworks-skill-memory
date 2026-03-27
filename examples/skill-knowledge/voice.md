# voice — experience

> Hands-on experience accumulated while using the voice skill.
> Max 30 entries; oldest are dropped when the limit is reached. Last updated: 2026-03-27

## Entries

- [Install first] If `agent-voice` is not found, run `npm install -g agent-voice` before any voice command. The skill does not auto-install the dependency.
- [Auth flow is interactive] If authentication fails, tell the user to run `agent-voice auth` in a separate terminal. Do NOT attempt to run auth yourself — it requires interactive terminal input and will hang.
- [ask vs say] Use `agent-voice ask` when you need user input (it captures the spoken response). Use `agent-voice say` for one-way announcements. Combine info + question into a single `ask` call to reduce latency.
- [User is not watching] During voice mode the user is listening, not reading. Never output markdown, code blocks, or long text — speak in short conversational sentences.
- [Session ends on signal] Voice mode ends when the user says "goodbye", "stop", "end voice", or types in the terminal. Always say goodbye before exiting and resume normal text interaction.
- [Latency] Each `agent-voice` call has noticeable latency (TTS + STT round trip). Batch information into fewer, longer `say` calls rather than many short ones.
