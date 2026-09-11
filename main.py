import json

from langchain_core.messages import AIMessage, ToolMessage
from langgraph.errors import GraphRecursionError

from agent.investigator import build_investigator
from agent.tools.patch_tools import propose_patch


def display_message(message):
    if isinstance(message, AIMessage):
        for call in message.tool_calls:
            print(f"\nTOOL REQUEST: {call['name']}")
            print(json.dumps(call["args"], indent=2))

        if message.content:
            print("\nAGENT RESPONSE:")
            print(message.content)

        if not message.tool_calls and not message.content:
            print("\nMODEL RETURNED AN EMPTY RESPONSE")
            print(
                "Finish reason:",
                message.response_metadata.get(
                    "finish_reason",
                    "not provided",
                ),
            )

    elif isinstance(message, ToolMessage):
        print(f"\nTOOL RESULT: {message.name}")
        print(message.content)


def main():
    agent = build_investigator()

    issue = (
        "A customer reports that checkout charges the wrong amount "
        "when the SAVE10 coupon is used. Investigate the repository, "
        "reproduce the failure, and explain the root cause with "
        "source-code evidence. Recommend a minimal fix."
    )

    messages = [{"role": "user", "content": issue}]

    print("Starting repository investigation...\n")

    for attempt in range(2):
        seen_messages = len(messages)
        final_state = None

        try:
            for state in agent.stream(
                {"messages": messages},
                config={"recursion_limit": 30},
                stream_mode="values",
            ):
                current_messages = state["messages"]

                for message in current_messages[seen_messages:]:
                    display_message(message)

                seen_messages = len(current_messages)
                final_state = state

        except GraphRecursionError:
            print("\nINCOMPLETE: Investigation step limit reached.")
            return

        if not final_state:
            print("\nINCOMPLETE: No agent state returned.")
            return

        messages = list(final_state["messages"])
        last_message = messages[-1]

        if not isinstance(last_message, AIMessage):
            print("\nINCOMPLETE: Run ended without a model response.")
            return

        if last_message.tool_calls:
            print("\nINCOMPLETE: Run ended with pending tool calls.")
            return

        if last_message.content:
            print("\nInvestigation response received.")

            if not isinstance(last_message.content, str):
                  print("Cannot propose a patch: expected a text report.")
                  return

            print("\nGenerating a patch proposal...")

            proposal = propose_patch(last_message.content)

            print("\nPROPOSED CHANGE:")
            print(proposal["explanation"])

            print("\nDIFF:")
            print(proposal["diff"])

            print("\nProposal saved:", proposal["proposal_file"])
            print("Status:", proposal["verification"])
            return
            print(
                "\nResponse received. Review the report "
                "against the tool evidence."
            )
            return

        if attempt == 0:
            print("\nEmpty response: continuing once with prior evidence.")

            # Remove only the empty final assistant message.
            messages.pop()

            messages.append({
                "role": "user",
                "content": (
                    "Your previous response was empty. Continue the "
                    "investigation using the evidence already gathered. "
                    "Run the relevant tests if you have not done so, "
                    "read any missing source files, and provide your "
                    "report. If blocked, explicitly explain the blocker."
                ),
            })
        else:
            print(
                "\nINCOMPLETE: The model returned an empty response "
                "again. Stopping after one retry."
            )
    agent = build_investigator()

    issue = (
        "A customer reports that checkout charges the wrong amount "
        "when the SAVE10 coupon is used. Investigate the repository, "
        "reproduce the failure, and explain the root cause with "
        "source-code evidence. Recommend a minimal fix."
    )

    print("Starting repository investigation...\n")

    seen_messages = 0
    final_state = None

    try:
        for state in agent.stream(
            {
                "messages": [
                    {"role": "user", "content": issue}
                ]
            },
            config={"recursion_limit": 30},
            stream_mode="values",
        ):
            messages = state["messages"]

            for message in messages[seen_messages:]:
                display_message(message)

            seen_messages = len(messages)
            final_state = state

    except GraphRecursionError:
        print(
            "\nINCOMPLETE: The investigation reached its step limit."
        )
        return

    if not final_state:
        print("\nINCOMPLETE: No agent state was returned.")
        return

    last_message = final_state["messages"][-1]

    has_final_response = (
        isinstance(last_message, AIMessage)
        and not last_message.tool_calls
        and bool(last_message.content)
    )

    if has_final_response:
        print(
            "\nInvestigation response received. "
            "Check its claims against the tool evidence."
        )
    else:
        print(
            "\nINCOMPLETE: The agent ended without a final report."
        )


if __name__ == "__main__":
    main()