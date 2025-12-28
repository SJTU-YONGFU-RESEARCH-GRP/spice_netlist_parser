#!/usr/bin/env bash

# Run the parser against all netlist samples in ./examples and capture logs.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLES_DIR="${SCRIPT_DIR}/examples/logic"
LOG_DIR="${EXAMPLES_DIR}/"
NETLIST_PARSER="${SCRIPT_DIR}/netlist_parser.sh"

if [ ! -d "${EXAMPLES_DIR}" ]; then
  echo "Examples directory not found at ${EXAMPLES_DIR}"
  exit 1
fi

if [ ! -x "${NETLIST_PARSER}" ]; then
  echo "netlist_parser.sh is missing or not executable at ${NETLIST_PARSER}"
  exit 1
fi

mkdir -p "${LOG_DIR}"

# Collect netlist files (.sp and .cdl); exit early if none found.
shopt -s nullglob
mapfile -t SP_FILES < <(cd "${EXAMPLES_DIR}" && printf "%s\n" *.sp | sort)
mapfile -t CDL_FILES < <(cd "${EXAMPLES_DIR}" && printf "%s\n" *.cdl | sort)
shopt -u nullglob

TOTAL_FILES=$((${#SP_FILES[@]} + ${#CDL_FILES[@]}))

if [ ${TOTAL_FILES} -eq 0 ]; then
  echo "No .sp or .cdl files found in ${EXAMPLES_DIR}"
  exit 0
fi

echo "Running regression across ${TOTAL_FILES} netlists in ${EXAMPLES_DIR}"
echo "  - ${#SP_FILES[@]} .sp files"
echo "  - ${#CDL_FILES[@]} .cdl files"
echo "Logs will be written to ${LOG_DIR}"
echo ""

STATUS=0

# Process .sp files
for netlist in "${SP_FILES[@]}"; do
  input_path="${EXAMPLES_DIR}/${netlist}"
  log_path="${LOG_DIR}/${netlist}.log"
  output_path="${LOG_DIR}/${netlist%.sp}.json"
  compare_output_path="${LOG_DIR}/${netlist%.sp}.json"

  echo "→ ${netlist}"
  run_status=0
  parse_status=0
  compare_status=0
  {
    echo "# $(date -Iseconds)"
    echo "# Input: ${input_path}"
    echo "# JSON output: ${output_path}"
    echo "# Compare output: ${compare_output_path}"
    if [ $# -gt 0 ]; then
      echo "# Extra args: $*"
    fi
    echo "# Command (parse): ${NETLIST_PARSER} \"${input_path}\" --format json --output \"${output_path}\" $*"
    echo "------------------------------------------------------------"
    "${NETLIST_PARSER}" "${input_path}" --format json --output "${output_path}" "$@" || parse_status=$?
    echo ""
    echo "# Command (compare): ${NETLIST_PARSER} \"${input_path}\" --compare \"${input_path}\" --compare-format json --compare-output \"${compare_output_path}\" $*"
    echo "------------------------------------------------------------"
    "${NETLIST_PARSER}" "${input_path}" --compare "${input_path}" --compare-format json --compare-output "${compare_output_path}" "$@" || compare_status=$?
  } >"${log_path}" 2>&1

  if [ ${parse_status} -ne 0 ] || [ ${compare_status} -ne 0 ]; then
    run_status=1
  fi

  # Check for warnings in the log file
  has_warnings=0
  if [ -f "${log_path}" ] && grep -qi "WARNING" "${log_path}"; then
    has_warnings=1
  fi

  if [ ${run_status} -eq 0 ]; then
    if [ ${has_warnings} -eq 1 ]; then
      echo "   ⚠️  Log: ${log_path} (warnings detected)"
    else
      echo "   ✅ Log: ${log_path}"
    fi
  else
    echo "   ⚠️  Failed (see ${log_path})"
    STATUS=1
  fi
done

# Process .cdl files
for netlist in "${CDL_FILES[@]}"; do
  input_path="${EXAMPLES_DIR}/${netlist}"
  log_path="${LOG_DIR}/${netlist}.log"
  output_path="${LOG_DIR}/${netlist%.cdl}.json"
  compare_output_path="${LOG_DIR}/${netlist%.cdl}.json"

  echo "→ ${netlist}"
  run_status=0
  parse_status=0
  compare_status=0
  {
    echo "# $(date -Iseconds)"
    echo "# Input: ${input_path}"
    echo "# JSON output: ${output_path}"
    echo "# Compare output: ${compare_output_path}"
    if [ $# -gt 0 ]; then
      echo "# Extra args: $*"
    fi
    echo "# Command (parse): ${NETLIST_PARSER} \"${input_path}\" --format json --output \"${output_path}\" $*"
    echo "------------------------------------------------------------"
    "${NETLIST_PARSER}" "${input_path}" --format json --output "${output_path}" "$@" || parse_status=$?
    echo ""
    echo "# Command (compare): ${NETLIST_PARSER} \"${input_path}\" --compare \"${input_path}\" --compare-format json --compare-output \"${compare_output_path}\" $*"
    echo "------------------------------------------------------------"
    "${NETLIST_PARSER}" "${input_path}" --compare "${input_path}" --compare-format json --compare-output "${compare_output_path}" "$@" || compare_status=$?
  } >"${log_path}" 2>&1

  if [ ${parse_status} -ne 0 ] || [ ${compare_status} -ne 0 ]; then
    run_status=1
  fi

  # Check for warnings in the log file
  has_warnings=0
  if [ -f "${log_path}" ] && grep -qi "WARNING" "${log_path}"; then
    has_warnings=1
  fi

  if [ ${run_status} -eq 0 ]; then
    if [ ${has_warnings} -eq 1 ]; then
      echo "   ⚠️  Log: ${log_path} (warnings detected)"
    else
      echo "   ✅ Log: ${log_path}"
    fi
  else
    echo "   ⚠️  Failed (see ${log_path})"
    STATUS=1
  fi
done

if [ ${STATUS} -eq 0 ]; then
  echo ""
  echo "All regression runs succeeded."
else
  echo ""
  echo "One or more regression runs failed. See logs in ${LOG_DIR}."
fi

exit ${STATUS}
