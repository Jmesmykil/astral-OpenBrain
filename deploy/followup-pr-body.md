Follow-up to #361. Three things from the review.

Mass, radius and diameter for the Sun, the Moon and every planet, straight off the body table that escape velocity and surface gravity already use. "mass of earth", "diameter of mars", "how big is jupiter", "mass of the moon in pounds". Radii are equatorial, so the diameters match NASA's published figures to the digit. Each one is pinned byte-exact.

The engine source and tests now ship next to main.py, in hub/. main.py is generated from them (python3 hub/build_ability.py) and hub/test_artifact_parity.py proves the shipped file answers every phrase the way the source does. hub/test_golden.py pins 155 phrases byte for byte, the ones it must stay silent on included. hub/test_hardening.py fuzzes four thousand utterances and rechecks every result a second way.

The timezone fallback and the Optional annotations you added are kept as you wrote them. The parity test now checks the other direction: the file must not carry the future import, the engine must not use a PEP 604 union, and the generated region is executed with nothing added, so a str | None fails on 3.9 in the test instead of on a device.

One line of the normalize docstring lost its last word in the merge. Restored.
