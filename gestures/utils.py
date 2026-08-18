import math
from tracking.hand_tracker import HandFrame

def is_finger_extended(hand_frame: HandFrame, mcp_idx: int, tip_idx: int, threshold: float = 1.2) -> bool:
    """
    Returns True if the finger is extended, False if it is curled.
    Calculates the 3D distance from the wrist to the tip and compares it
    to the distance from the wrist to the MCP joint.
    """
    wrist = hand_frame.wrist
    mcp = hand_frame.landmarks[mcp_idx]
    tip = hand_frame.landmarks[tip_idx]
    
    dist_tip = math.dist((wrist.x, wrist.y, wrist.z), (tip.x, tip.y, tip.z))
    dist_mcp = math.dist((wrist.x, wrist.y, wrist.z), (mcp.x, mcp.y, mcp.z))
    
    # If the distance from wrist to tip is significantly larger than wrist to MCP,
    # the finger is considered extended.
    return dist_tip > (dist_mcp * threshold)
