#!/bin/bash
# AWS Coworker banner script
# Called by the `coworker` launcher before dropping into Claude Code
# Run standalone: bash .claude/scripts/session-start.sh

ORANGE='\033[38;5;208m'
YELLOW='\033[38;5;220m'
WHITE='\033[1;37m'
DIM='\033[2m'
RESET='\033[0m'

echo ""
echo -e "${ORANGE}  ╔════════════════════════════════════════════════════╗${RESET}"
echo -e "${ORANGE}  ║${RESET}                                                    ${ORANGE}║${RESET}"
echo -e "${ORANGE}  ║${RESET}   ${YELLOW}┏━┓╻ ╻┏━┓${RESET}   ${WHITE}┏━╸┏━┓╻ ╻┏━┓┏━┓╻┏ ┏━╸┏━┓${RESET}             ${ORANGE}║${RESET}"
echo -e "${ORANGE}  ║${RESET}   ${YELLOW}┣━┫┃╻┃┗━┓${RESET}   ${WHITE}┃  ┃ ┃┃╻┃┃ ┃┣┳┛┣┻┓┣╸ ┣┳┛${RESET}             ${ORANGE}║${RESET}"
echo -e "${ORANGE}  ║${RESET}   ${YELLOW}╹ ╹┗┻┛┗━┛${RESET}   ${WHITE}┗━╸┗━┛┗┻┛┗━┛╹┗╸╹ ╹┗━╸╹┗╸${RESET}             ${ORANGE}║${RESET}"
echo -e "${ORANGE}  ║${RESET}                                                    ${ORANGE}║${RESET}"
echo -e "${ORANGE}  ║${RESET}   ${DIM}Enterprise AWS Infrastructure Management${RESET}         ${ORANGE}║${RESET}"
echo -e "${ORANGE}  ║${RESET}   ${DIM}Powered by Claude Code${RESET}                           ${ORANGE}║${RESET}"
echo -e "${ORANGE}  ║${RESET}                                                    ${ORANGE}║${RESET}"
echo -e "${ORANGE}  ╚════════════════════════════════════════════════════╝${RESET}"
echo ""
