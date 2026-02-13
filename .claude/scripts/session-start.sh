#!/bin/bash
# AWS Coworker session start banner
# Displayed via Claude Code SessionStart hook

ORANGE='\033[38;5;208m'
YELLOW='\033[38;5;220m'
WHITE='\033[1;37m'
DIM='\033[2m'
RESET='\033[0m'

echo ""
echo -e "${ORANGE}     ╔═══════════════════════════════════════════════════╗${RESET}"
echo -e "${ORANGE}     ║${RESET}                                                   ${ORANGE}║${RESET}"
echo -e "${ORANGE}     ║${RESET}   ${YELLOW}  ▄▄▄  █   █ █▀▀▀  ${WHITE}█▀▀▀ █▀▀█ █   █ █▀▀█ █▀▀█ █▀▀█${RESET}  ${ORANGE}║${RESET}"
echo -e "${ORANGE}     ║${RESET}   ${YELLOW}  █▄█  █ █ █ ▀▀▀█  ${WHITE}█    █  █ █ █ █ █  █ █▄▄▀ █▄▄▀${RESET}  ${ORANGE}║${RESET}"
echo -e "${ORANGE}     ║${RESET}   ${YELLOW}  █ █  █▄█▄█ ▀▀▀█  ${WHITE}█▄▄▄ █▄▄█ █▄█▄█ █▄▄█ █  █ █  █${RESET}  ${ORANGE}║${RESET}"
echo -e "${ORANGE}     ║${RESET}                                                   ${ORANGE}║${RESET}"
echo -e "${ORANGE}     ║${RESET}   ${DIM}Enterprise AWS Infrastructure Management${RESET}          ${ORANGE}║${RESET}"
echo -e "${ORANGE}     ║${RESET}   ${DIM}Powered by Claude Code${RESET}                            ${ORANGE}║${RESET}"
echo -e "${ORANGE}     ║${RESET}                                                   ${ORANGE}║${RESET}"
echo -e "${ORANGE}     ╚═══════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  ${DIM}Commands:${RESET}"
echo -e "    ${WHITE}/aws-coworker-plan-interaction${RESET}    ${DIM}Plan any AWS operation${RESET}"
echo -e "    ${WHITE}/aws-coworker-execute-nonprod${RESET}     ${DIM}Execute approved plans${RESET}"
echo -e "    ${WHITE}/aws-coworker-prepare-prod-change${RESET} ${DIM}Production via CI/CD${RESET}"
echo -e "    ${WHITE}/aws-coworker-audit-library${RESET}       ${DIM}Audit system health${RESET}"
echo ""
