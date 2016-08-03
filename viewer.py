import numpy as np
import matplotlib.pyplot as plt
import sys

sys.path.append("..")
from geo_viewer.RTCMv3_decode import decode_rtcm3_from_net, set_generator


# plt.xlim(0, 50)
# plt.ylim(0, 1)
# plt.ion()
# y = []
# i = 0
# while True:
#     temp = np.random.random()
#     i += 1
#     y.append(temp)
#     if i > 50:
#         plt.xlim(i - 50, i)
#     plt.plot(y, color='green')
#     plt.pause(0.05)

def decode_rtcm_stream(data):
    if len(data) > 0:
        decode_rtcm3_from_net(data)
