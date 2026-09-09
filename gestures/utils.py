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

def finger_curl(hand_frame: HandFrame, mcp_idx: int, pip_idx: int, tip_idx: int) -> float:
    """
    Computes vector A = pip - mcp (proximal segment)
    Computes vector B = tip - pip (distal segment)
    Returns the normalized dot product (cosine of the angle) between A and B
       - ~1.0 = finger fully straight
       - ~0.0 = bent ~90 degrees
       - negative = folded back on itself
    """
    mcp = hand_frame.landmarks[mcp_idx]
    pip = hand_frame.landmarks[pip_idx]
    tip = hand_frame.landmarks[tip_idx]

    A = (pip.x - mcp.x, pip.y - mcp.y, pip.z - mcp.z)
    B = (tip.x - pip.x, tip.y - pip.y, tip.z - pip.z)

    dot_product = A[0]*B[0] + A[1]*B[1] + A[2]*B[2]
    magA = math.sqrt(A[0]**2 + A[1]**2 + A[2]**2)
    magB = math.sqrt(B[0]**2 + B[1]**2 + B[2]**2)

    if magA == 0 or magB == 0:
        return 0.0

    return dot_product / (magA * magB)

def is_finger_extended_by_curl(hand_frame: HandFrame, mcp_idx: int, pip_idx: int, tip_idx: int, curl_threshold: float = 0.5) -> bool:
    return finger_curl(hand_frame, mcp_idx, pip_idx, tip_idx) > curl_threshold
