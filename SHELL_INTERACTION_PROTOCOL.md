# Shell Interaction Protocol

## Purpose
This protocol prevents accidental shell execution errors caused by pasting explanatory text into PowerShell, CMD, Bash, or any other terminal.

## Mandatory Rule
Executable shell blocks must contain only valid shell content.

## Allowed In Executable Blocks
- commands
- valid script syntax
- environment assignments
- safe English comments when needed

## Prohibited In Executable Blocks
- Persian prose
- human instructions
- bullet lists that are not shell comments
- markdown headings
- expected-output descriptions
- explanatory sentences

## Required Response Format For Shell Work
1. Explain the intent outside the executable block.
2. Provide one copy-paste-ready executable block.
3. Put expected output and interpretation outside the executable block.
4. Ask for only the required output after the executable block.

## Comment Rule
If comments are needed inside executable shell blocks, they must be valid comments for that shell and written in English.

## PowerShell Safety Rule
Never paste plain Persian text, markdown bullets, or explanatory sentences into PowerShell. PowerShell treats them as commands or expressions.

## Agent Obligation
Any future agent that provides shell commands for this project must follow this protocol.
