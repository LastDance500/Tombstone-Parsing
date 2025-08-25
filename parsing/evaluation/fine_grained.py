import os
import re
import json

from utils.smatch import score_amr_pairs

if __name__ == '__main__':
    # 1. 定义各维度对应的图片文件名列表
    language_images = [
        't00424.jpg', 't01010.jpg', 't00816.jpg', 't00712.jpg', 't00592.jpg',
        't01176.jpg', 't00830.jpg', 't01177.jpg', 't00105.jpg', 't01178.jpg',
        't00567.jpg', 't00982.jpg', 't00181.jpg', 't00981.jpgt00440.jpg',
        't01191.jpg', 't00795.jpg', 't01142.jpg', 't00514.jpg', 't01190.jpg'
    ]
    language_images.sort()
    print("language_images:", language_images)

    font_style_images = (
            ['t00980.jpg', 't00849.jpg', 't01096.jpg', 't01029.jpg', 't01171.jpg',
             't00982.jpg', 't01027.jpg', 't01155.jpg', 't00759.jpg', 't00949.jpg',
             't00758.jpg', 't01036.jpg'] +
            ['t00318.jpg', 't00516.jpg', 't01109.jpg', 't01124.jpg', 't01103.jpg',
             't01178.jpg', 't00567.jpg', 't00890.jpg', 't01172.jpg', 't00963.jpg',
             't00803.jpg', 't00181.jpg', 't00713.jpg', 't01100.jpg', 't00453.jpg',
             't01191.jpg', 't00095.jpg', 't00523.jpg', 't01101.jpg', 't00652.jpg',
             't00514.jpg', 't00685.jpg', 't01190.jpg'] +
            ['t01083.jpg', 't00257.jpg']
    )
    font_style_images.sort()
    print("font_style_images:", font_style_images)

    rhetorical_devices_images = [
        't00424.jpg', 't00980.jpg', 't00781.jpg', 't00775.jpg', 't01013.jpg',
        't00806.jpg', 't00407.jpg', 't00519.jpg', 't00943.jpg', 't00444.jpg',
        't00573.jpg', 't01062.jpg', 't00659.jpg', 't00722.jpg', 't00555.jpg',
        't01116.jpg', 't01025.jpg', 't00059.jpg', 't01161.jpg', 't00168.jpg',
        't00347.jpg', 't00764.jpg', 't00596.jpg', 't00446.jpg', 't00830.jpg',
        't00936.jpg', 't01115.jpg', 't00437.jpg', 't01111.jpg', 't00850.jpg',
        't01123.jpg', 't01027.jpg', 't00854.jpg', 't01099.jpg', 't00998.jpg',
        't00189.jpg', 't00440.jpg', 't01130.jpg', 't00876.jpg', 't00856.jpg',
        't01006.jpg', 't01010.jpg', 't00039.jpg', 't00836.jpg', 't00741.jpg',
        't00254.jpg', 't00574.jpg', 't00727.jpg', 't00182.jpg', 't00549.jpg',
        't00535.jpg', 't00040.jpg', 't00964.jpg', 't00900.jpg', 't00170.jpg',
        't00660.jpg', 't00514.jpg', 't00365.jpg', 't00821.jpg', 't00257.jpg',
        't01169.jpg', 't00145.jpg', 't00234.jpg', 't00948.jpg', 't00687.jpg',
        't00810.jpg', 't00939.jpg', 't00949.jpg', 't00780.jpg', 't00887.jpg',
        't00833.jpg', 't00888.jpg', 't00594.jpg', 't00880.jpg', 't00096.jpg'
    ]
    rhetorical_devices_images.sort()
    print("rhetorical_devices_images:", rhetorical_devices_images)

    syntactic_complexity_images = [
        't00980.jpg', 't00775.jpg', 't01013.jpg', 't00806.jpg', 't00774.jpg',
        't00219.jpg', 't00659.jpg', 't00722.jpg', 't01116.jpg', 't01025.jpg',
        't00168.jpg', 't00764.jpg', 't00596.jpg', 't00830.jpg', 't01115.jpg',
        't00437.jpg', 't00850.jpg', 't01123.jpg', 't00854.jpg', 't01006.jpg',
        't00039.jpg', 't00727.jpg', 't00182.jpg', 't00549.jpg', 't00040.jpg',
        't00660.jpg', 't00257.jpg', 't01169.jpg', 't00145.jpg', 't00234.jpg',
        't00948.jpg', 't00810.jpg', 't00949.jpg', 't00888.jpg', 't00594.jpg',
        't00880.jpg'
    ]
    syntactic_complexity_images.sort()
    print("syntactic_complexity_images:", syntactic_complexity_images)

    figurative_language_images = [
        't00424.jpg', 't00980.jpg', 't00781.jpg', 't00775.jpg', 't01013.jpg',
        't00407.jpg', 't00710.jpg', 't00519.jpg', 't00943.jpg', 't00444.jpg',
        't00573.jpg', 't01062.jpg', 't00659.jpg', 't00722.jpg', 't01178.jpg',
        't00555.jpg', 't01116.jpg', 't01025.jpg', 't00323.jpg', 't01161.jpg',
        't00168.jpg', 't01172.jpg', 't00347.jpg', 't00764.jpg', 't00596.jpg',
        't00446.jpg', 't00830.jpg', 't01115.jpg', 't01111.jpg', 't00850.jpg',
        't01123.jpg', 't01027.jpg', 't00854.jpg', 't01099.jpg', 't00998.jpg',
        't00189.jpg', 't00440.jpg', 't01130.jpg', 't00876.jpg', 't00856.jpg',
        't01006.jpg', 't01010.jpg', 't00039.jpg', 't00836.jpg', 't00254.jpg',
        't00727.jpg', 't00182.jpg', 't00549.jpg', 't00535.jpg', 't00040.jpg',
        't00964.jpg', 't00900.jpg', 't00660.jpg', 't00514.jpg', 't00365.jpg',
        't00821.jpg', 't00257.jpg', 't01169.jpg', 't00145.jpg', 't00234.jpg',
        't00948.jpg', 't00687.jpg', 't00810.jpg', 't00939.jpg', 't00887.jpg',
        't00833.jpg', 't00888.jpg', 't00594.jpg', 't00880.jpg', 't00096.jpg'
    ]
    figurative_language_images.sort()
    print("figurative_language_images:", figurative_language_images)

    anaphoric_deictic_pronouns = ['t00980.jpg', 't00592.jpg', 't00913.jpg', 't00775.jpg', 't00109.jpg', 't01013.jpg',
                                  't00013.jpg', 't00676.jpg', 't00327.jpg', 't00025.jpg', 't00997.jpg', 't00970.jpg',
                                  't00407.jpg', 't00064.jpg', 't00161.jpg', 't00288.jpg', 't00250.jpg', 't00875.jpg',
                                  't00373.jpg', 't00333.jpg', 't00105.jpg', 't00201.jpg', 't00075.jpg', 't00835.jpg',
                                  't00268.jpg', 't00137.jpg', 't00484.jpg', 't00646.jpg', 't01193.jpg', 't00043.jpg',
                                  't00493.jpg', 't01048.jpg', 't00885.jpg', 't00100.jpg', 't00198.jpg', 't00490.jpg',
                                  't00558.jpg', 't00488.jpg', 't00070.jpg', 't01009.jpg', 't00519.jpg', 't00987.jpg',
                                  't00943.jpg', 't00516.jpg', 't00405.jpg', 't00879.jpg', 't00329.jpg', 't00267.jpg',
                                  't00009.jpg', 't00065.jpg', 't01045.jpg', 't00826.jpg', 't00138.jpg', 't01007.jpg',
                                  't00546.jpg', 't00774.jpg', 't00444.jpg', 't00146.jpg', 't00849.jpg', 't01135.jpg',
                                  't00330.jpg', 't00357.jpg', 't00197.jpg', 't00914.jpg', 't01062.jpg', 't00142.jpg',
                                  't01057.jpg', 't00415.jpg', 't00659.jpg', 't00722.jpg', 't00760.jpg', 't01051.jpg',
                                  't00151.jpg', 't00960.jpg', 't00945.jpg', 't00882.jpg', 't00001.jpg', 't01043.jpg',
                                  't01118.jpg', 't00456.jpg', 't00324.jpg', 't00343.jpg', 't00194.jpg', 't01065.jpg',
                                  't00312.jpg', 't00908.jpg', 't00124.jpg', 't01148.jpg', 't01167.jpg', 't00074.jpg',
                                  't00127.jpg', 't00505.jpg', 't00583.jpg', 't01120.jpg', 't01197.jpg', 't00608.jpg',
                                  't00209.jpg', 't00979.jpg', 't00667.jpg', 't00183.jpg', 't00062.jpg', 't00674.jpg',
                                  't00086.jpg', 't00023.jpg', 't00448.jpg', 't00555.jpg', 't00411.jpg', 't00336.jpg',
                                  't00570.jpg', 't01116.jpg', 't00141.jpg', 't00323.jpg', 't01171.jpg', 't00059.jpg',
                                  't00131.jpg', 't00990.jpg', 't00940.jpg', 't00669.jpg', 't00060.jpg', 't00695.jpg',
                                  't01019.jpg', 't00707.jpg', 't00473.jpg', 't00720.jpg', 't01087.jpg', 't00520.jpg',
                                  't00224.jpg', 't01020.jpg', 't01117.jpg', 't00569.jpg', 't00865.jpg', 't00803.jpg',
                                  't00347.jpg', 't00764.jpg', 't00321.jpg', 't01105.jpg', 't00441.jpg', 't00596.jpg',
                                  't00134.jpg', 't00656.jpg', 't01129.jpg', 't00924.jpg', 't00082.jpg', 't00270.jpg',
                                  't00003.jpg', 't00734.jpg', 't00228.jpg', 't00830.jpg', 't00243.jpg', 't00648.jpg',
                                  't00122.jpg', 't00353.jpg', 't00936.jpg', 't01198.jpg', 't01055.jpg', 't00679.jpg',
                                  't00418.jpg', 't00252.jpg', 't00492.jpg', 't00884.jpg', 't01115.jpg', 't00292.jpg',
                                  't00437.jpg', 't00158.jpg', 't00077.jpg', 't01111.jpg', 't00530.jpg', 't00358.jpg',
                                  't01073.jpg', 't00732.jpg', 't00069.jpg', 't00850.jpg', 't00271.jpg', 't01098.jpg',
                                  't00110.jpg', 't00283.jpg', 't01123.jpg', 't00378.jpg', 't01027.jpg', 't00303.jpg',
                                  't00163.jpg', 't00481.jpg', 't00190.jpg', 't00866.jpg', 't00999.jpg', 't01192.jpg',
                                  't01099.jpg', 't00937.jpg', 't00447.jpg', 't00150.jpg', 't00589.jpg', 't00136.jpg',
                                  't00828.jpg', 't01097.jpg', 't00408.jpg', 't01130.jpg', 't00598.jpg', 't00553.jpg',
                                  't00008.jpg', 't00002.jpg', 't00625.jpg', 't01151.jpg', 't00486.jpg', 't00054.jpg',
                                  't00753.jpg', 't00955.jpg', 't00638.jpg', 't00435.jpg', 't01006.jpg', 't00675.jpg',
                                  't00682.jpg', 't00829.jpg', 't01090.jpg', 't00748.jpg', 't01104.jpg', 't01095.jpg',
                                  't00388.jpg', 't00906.jpg', 't00165.jpg', 't00506.jpg', 't00429.jpg', 't00988.jpg',
                                  't00526.jpg', 't00609.jpg', 't00039.jpg', 't00233.jpg', 't00340.jpg', 't00692.jpg',
                                  't00836.jpg', 't00497.jpg', 't00242.jpg', 't00741.jpg', 't01127.jpg', 't00391.jpg',
                                  't00313.jpg', 't00240.jpg', 't00600.jpg', 't00539.jpg', 't00745.jpg', 't01067.jpg',
                                  't00969.jpg', 't00740.jpg', 't00574.jpg', 't00143.jpg', 't00711.jpg', 't00727.jpg',
                                  't00182.jpg', 't00173.jpg', 't00549.jpg', 't00782.jpg', 't00111.jpg', 't00518.jpg',
                                  't00040.jpg', 't00754.jpg', 't00964.jpg', 't00351.jpg', 't00028.jpg', 't00005.jpg',
                                  't00689.jpg', 't00601.jpg', 't00986.jpg', 't01126.jpg', 't00900.jpg', 't00120.jpg',
                                  't00680.jpg', 't00350.jpg', 't00864.jpg', 't00660.jpg', 't00733.jpg', 't00521.jpg',
                                  't00133.jpg', 't00514.jpg', 't00636.jpg', 't00433.jpg', 't01163.jpg', 't00365.jpg',
                                  't00412.jpg', 't00709.jpg', 't00000.jpg', 't00686.jpg', 't00393.jpg', 't00222.jpg',
                                  't00257.jpg', 't00621.jpg', 't00501.jpg', 't00291.jpg', 't00771.jpg', 't00359.jpg',
                                  't01165.jpg', 't00093.jpg', 't00203.jpg', 't00597.jpg', 't00507.jpg', 't00517.jpg',
                                  't00899.jpg', 't00083.jpg', 't00186.jpg', 't00015.jpg', 't00187.jpg', 't00772.jpg',
                                  't01005.jpg', 't00409.jpg', 't00315.jpg', 't00006.jpg', 't01147.jpg', 't00819.jpg',
                                  't00582.jpg', 't00565.jpg', 't00467.jpg', 't01082.jpg', 't01018.jpg', 't00178.jpg',
                                  't00071.jpg', 't00159.jpg', 't00234.jpg', 't00394.jpg', 't00629.jpg', 't00948.jpg',
                                  't00436.jpg', 't00260.jpg', 't00673.jpg', 't00687.jpg', 't00215.jpg', 't00166.jpg',
                                  't00759.jpg', 't00683.jpg', 't00218.jpg', 't00810.jpg', 't00191.jpg', 't00743.jpg',
                                  't00561.jpg', 't00566.jpg', 't00788.jpg', 't01152.jpg', 't00196.jpg', 't00478.jpg',
                                  't00949.jpg', 't00590.jpg', 't00366.jpg', 't00833.jpg', 't00888.jpg', 't00576.jpg',
                                  't00626.jpg', 't00932.jpg', 't00912.jpg', 't00410.jpg', 't00758.jpg', 't00880.jpg',
                                  't00096.jpg', 't00765.jpg', 't00995.jpg', 't00285.jpg', 't00307.jpg', 't00584.jpg',
                                  't00972.jpg', 't00476.jpg', 't00058.jpg', 't00106.jpg', 't00014.jpg']

    anaphoric_deictic_pronouns.sort()
    print("anaphoric_deictic_pronouns:", anaphoric_deictic_pronouns)

    abbreviated_names = ['t00208.jpg', 't00980.jpg', 't00802.jpg', 't00109.jpg', 't00013.jpg', 't00676.jpg',
                         't00327.jpg', 't00970.jpg', 't00407.jpg', 't00161.jpg', 't00875.jpg', 't00373.jpg',
                         't00333.jpg', 't00710.jpg', 't00201.jpg', 't00663.jpg', 't01039.jpg', 't00137.jpg',
                         't00484.jpg', 't00646.jpg', 't00457.jpg', 't00493.jpg', 't00338.jpg', 't01048.jpg',
                         't00198.jpg', 't01196.jpg', 't00488.jpg', 't00070.jpg', 't00318.jpg', 't00519.jpg',
                         't00943.jpg', 't00405.jpg', 't00746.jpg', 't00879.jpg', 't00088.jpg', 't00329.jpg',
                         't00009.jpg', 't00065.jpg', 't00965.jpg', 't00138.jpg', 't01007.jpg', 't00546.jpg',
                         't00444.jpg', 't00698.jpg', 't00465.jpg', 't00146.jpg', 't00849.jpg', 't00330.jpg',
                         't00357.jpg', 't00197.jpg', 't00914.jpg', 't01062.jpg', 't01096.jpg', 't01003.jpg',
                         't00415.jpg', 't00919.jpg', 't00102.jpg', 't01079.jpg', 't00471.jpg', 't00204.jpg',
                         't00151.jpg', 't00945.jpg', 't00827.jpg', 't00882.jpg', 't01043.jpg', 't01118.jpg',
                         't00543.jpg', 't00863.jpg', 't00248.jpg', 't00324.jpg', 't00343.jpg', 't01065.jpg',
                         't00312.jpg', 't00908.jpg', 't00124.jpg', 't01148.jpg', 't00422.jpg', 't00074.jpg',
                         't00127.jpg', 't00505.jpg', 't00583.jpg', 't01197.jpg', 't00608.jpg', 't00209.jpg',
                         't00979.jpg', 't00667.jpg', 't01103.jpg', 't00649.jpg', 't00183.jpg', 't01154.jpg',
                         't00086.jpg', 't00023.jpg', 't00555.jpg', 't00411.jpg', 't01029.jpg', 't00567.jpg',
                         't00290.jpg', 't00873.jpg', 't01070.jpg', 't00323.jpg', 't00135.jpg', 't00131.jpg',
                         't00664.jpg', 't00199.jpg', 't00563.jpg', 't00695.jpg', 't01172.jpg', 't01019.jpg',
                         't00707.jpg', 't00473.jpg', 't01020.jpg', 't01117.jpg', 't00865.jpg', 't00803.jpg',
                         't00347.jpg', 't00468.jpg', 't00321.jpg', 't00134.jpg', 't00656.jpg', 't00967.jpg',
                         't00924.jpg', 't00082.jpg', 't00243.jpg', 't00278.jpg', 't00648.jpg', 't00122.jpg',
                         't00353.jpg', 't00564.jpg', 't00936.jpg', 't01198.jpg', 't00611.jpg', 't01055.jpg',
                         't00362.jpg', 't00492.jpg', 't00432.jpg', 't00292.jpg', 't00358.jpg', 't01073.jpg',
                         't00732.jpg', 't00162.jpg', 't00181.jpg', 't00110.jpg', 't01145.jpg', 't01027.jpg',
                         't00024.jpg', 't00303.jpg', 't00163.jpg', 't00481.jpg', 't00190.jpg', 't00854.jpg',
                         't00866.jpg', 't00999.jpg', 't00302.jpg', 't00966.jpg', 't00937.jpg', 't00868.jpg',
                         't00869.jpg', 't00150.jpg', 't00136.jpg', 't00408.jpg', 't01130.jpg', 't00598.jpg',
                         't00553.jpg', 't00008.jpg', 't00876.jpg', 't00856.jpg', 't00957.jpg', 't00316.jpg',
                         't00747.jpg', 't01151.jpg', 't00486.jpg', 't00435.jpg', 't00152.jpg', 't00682.jpg',
                         't00829.jpg', 't00451.jpg', 't01090.jpg', 't01140.jpg', 't00840.jpg', 't01104.jpg',
                         't01095.jpg', 't00388.jpg', 't00548.jpg', 't00620.jpg', 't00165.jpg', 't00506.jpg',
                         't00413.jpg', 't00789.jpg', 't00895.jpg', 't00429.jpg', 't00988.jpg', 't01110.jpg',
                         't00609.jpg', 't00339.jpg', 't00039.jpg', 't00817.jpg', 't00340.jpg', 't00836.jpg',
                         't00816.jpg', 't00242.jpg', 't00741.jpg', 't00391.jpg', 't00313.jpg', 't00240.jpg',
                         't00745.jpg', 't01067.jpg', 't00740.jpg', 't00099.jpg', 't00254.jpg', 't00574.jpg',
                         't00095.jpg', 't00143.jpg', 't00711.jpg', 't00182.jpg', 't00173.jpg', 't00946.jpg',
                         't00372.jpg', 't00518.jpg', 't00964.jpg', 't00703.jpg', 't00247.jpg', 't00005.jpg',
                         't00689.jpg', 't00601.jpg', 't01126.jpg', 't00900.jpg', 't00326.jpg', 't00120.jpg',
                         't00350.jpg', 't00430.jpg', 't00864.jpg', 't00652.jpg', 't00733.jpg', 't00365.jpg',
                         't00709.jpg', 't00000.jpg', 't00686.jpg', 't00953.jpg', 't00309.jpg', 't00621.jpg',
                         't00501.jpg', 't00051.jpg', 't00291.jpg', 't00771.jpg', 't00359.jpg', 't00093.jpg',
                         't00203.jpg', 't00661.jpg', 't00597.jpg', 't00083.jpg', 't00015.jpg', 't00500.jpg',
                         't00187.jpg', 't00334.jpg', 't01005.jpg', 't00315.jpg', 't00527.jpg', 't00958.jpg',
                         't01147.jpg', 't00819.jpg', 't00582.jpg', 't00565.jpg', 't00467.jpg', 't00178.jpg',
                         't00071.jpg', 't00306.jpg', 't00394.jpg', 't00230.jpg', 't00948.jpg', 't00293.jpg',
                         't00436.jpg', 't00673.jpg', 't01132.jpg', 't00215.jpg', 't00859.jpg', 't00759.jpg',
                         't00683.jpg', 't00191.jpg', 't00743.jpg', 't00561.jpg', 't00677.jpg', 't00566.jpg',
                         't01152.jpg', 't00871.jpg', 't00196.jpg', 't00778.jpg', 't00478.jpg', 't00341.jpg',
                         't00475.jpg', 't01168.jpg', 't00887.jpg', 't00366.jpg', 't00833.jpg', 't00907.jpg',
                         't00626.jpg', 't00308.jpg', 't00180.jpg', 't00912.jpg', 't00047.jpg', 't00758.jpg',
                         't00042.jpg', 't00765.jpg', 't00995.jpg', 't00285.jpg', 't00307.jpg', 't00584.jpg',
                         't00106.jpg', 't01146.jpg']

    abbreviated_names.sort()
    print("abbreviated_names:", abbreviated_names)

    multiple_persons = ['t00980.jpg', 't00781.jpg', 't00802.jpg', 't00913.jpg', 't00109.jpg', 't01013.jpg',
                        't00013.jpg', 't00676.jpg', 't00327.jpg', 't01040.jpg', 't00061.jpg', 't00025.jpg',
                        't00997.jpg', 't00970.jpg', 't00407.jpg', 't00064.jpg', 't01176.jpg', 't00161.jpg',
                        't00459.jpg', 't00288.jpg', 't00469.jpg', 't00250.jpg', 't00094.jpg', 't00036.jpg',
                        't00333.jpg', 't00710.jpg', 't00105.jpg', 't00201.jpg', 't00075.jpg', 't00835.jpg',
                        't00644.jpg', 't00268.jpg', 't00137.jpg', 't00262.jpg', 't00484.jpg', 't00542.jpg',
                        't00646.jpg', 't01193.jpg', 't00951.jpg', 't00449.jpg', 't00493.jpg', 't00696.jpg',
                        't00885.jpg', 't00100.jpg', 't00198.jpg', 't00490.jpg', 't00558.jpg', 't00488.jpg',
                        't00070.jpg', 't00318.jpg', 't01009.jpg', 't00519.jpg', 't00987.jpg', 't00943.jpg',
                        't00516.jpg', 't00405.jpg', 't01137.jpg', 't00746.jpg', 't00879.jpg', 't00088.jpg',
                        't00329.jpg', 't00267.jpg', 't00065.jpg', 't00826.jpg', 't00138.jpg', 't01007.jpg',
                        't00546.jpg', 't00774.jpg', 't00797.jpg', 't00444.jpg', 't00698.jpg', 't00465.jpg',
                        't00146.jpg', 't01135.jpg', 't00330.jpg', 't00357.jpg', 't00197.jpg', 't00914.jpg',
                        't01062.jpg', 't00142.jpg', 't01057.jpg', 't01003.jpg', 't00415.jpg', 't00919.jpg',
                        't01051.jpg', 't00471.jpg', 't00052.jpg', 't00151.jpg', 't00960.jpg', 't00827.jpg',
                        't00978.jpg', 't00882.jpg', 't00001.jpg', 't01043.jpg', 't00543.jpg', 't00324.jpg',
                        't00343.jpg', 't01065.jpg', 't00312.jpg', 't00556.jpg', 't00908.jpg', 't00124.jpg',
                        't01148.jpg', 't01199.jpg', 't01167.jpg', 't00074.jpg', 't00127.jpg', 't00505.jpg',
                        't00583.jpg', 't01120.jpg', 't01197.jpg', 't00608.jpg', 't00209.jpg', 't00979.jpg',
                        't00667.jpg', 't00649.jpg', 't01178.jpg', 't00183.jpg', 't00062.jpg', 't01154.jpg',
                        't00086.jpg', 't00777.jpg', 't00023.jpg', 't00448.jpg', 't00555.jpg', 't00411.jpg',
                        't00336.jpg', 't01029.jpg', 't00570.jpg', 't01116.jpg', 't00141.jpg', 't01070.jpg',
                        't00323.jpg', 't01171.jpg', 't00059.jpg', 't00135.jpg', 't00990.jpg', 't00940.jpg',
                        't00752.jpg', 't00199.jpg', 't00669.jpg', 't00244.jpg', 't00060.jpg', 't00563.jpg',
                        't00695.jpg', 't01019.jpg', 't00707.jpg', 't00473.jpg', 't00977.jpg', 't00720.jpg',
                        't01087.jpg', 't00520.jpg', 't00224.jpg', 't01117.jpg', 't00569.jpg', 't00865.jpg',
                        't00347.jpg', 't00468.jpg', 't00764.jpg', 't00321.jpg', 't01105.jpg', 't00441.jpg',
                        't00134.jpg', 't00656.jpg', 't01129.jpg', 't00924.jpg', 't00249.jpg', 't00082.jpg',
                        't00270.jpg', 't00003.jpg', 't00734.jpg', 't00228.jpg', 't00416.jpg', 't00830.jpg',
                        't00243.jpg', 't00648.jpg', 't00122.jpg', 't00564.jpg', 't00936.jpg', 't01198.jpg',
                        't00611.jpg', 't01055.jpg', 't00362.jpg', 't00679.jpg', 't00418.jpg', 't00252.jpg',
                        't00432.jpg', 't01115.jpg', 't00551.jpg', 't00437.jpg', 't00158.jpg', 't00077.jpg',
                        't00530.jpg', 't00358.jpg', 't01092.jpg', 't01073.jpg', 't00069.jpg', 't00850.jpg',
                        't00271.jpg', 't00162.jpg', 't00903.jpg', 't01098.jpg', 't00118.jpg', 't00110.jpg',
                        't00283.jpg', 't01123.jpg', 't00378.jpg', 't00024.jpg', 't00572.jpg', 't00303.jpg',
                        't00163.jpg', 't00481.jpg', 't00190.jpg', 't00854.jpg', 't00866.jpg', 't00999.jpg',
                        't00302.jpg', 't01192.jpg', 't01099.jpg', 't00998.jpg', 't01004.jpg', 't00937.jpg',
                        't00440.jpg', 't00868.jpg', 't00447.jpg', 't00869.jpg', 't00150.jpg', 't00589.jpg',
                        't00217.jpg', 't00136.jpg', 't00828.jpg', 't00408.jpg', 't01130.jpg', 't00598.jpg',
                        't00553.jpg', 't00008.jpg', 't00002.jpg', 't00625.jpg', 't00957.jpg', 't01151.jpg',
                        't00486.jpg', 't00054.jpg', 't00753.jpg', 't00955.jpg', 't00638.jpg', 't00435.jpg',
                        't00152.jpg', 't00675.jpg', 't00682.jpg', 't00829.jpg', 't01090.jpg', 't01140.jpg',
                        't01000.jpg', 't00748.jpg', 't00840.jpg', 't01104.jpg', 't01181.jpg', 't01191.jpg',
                        't01095.jpg', 't00388.jpg', 't00906.jpg', 't00620.jpg', 't00165.jpg', 't00506.jpg',
                        't00413.jpg', 't00789.jpg', 't00895.jpg', 't00630.jpg', 't00429.jpg', 't00988.jpg',
                        't01110.jpg', 't00526.jpg', 't00339.jpg', 't00795.jpg', 't00233.jpg', 't00817.jpg',
                        't00340.jpg', 't00692.jpg', 't00836.jpg', 't00497.jpg', 't00242.jpg', 't00741.jpg',
                        't01127.jpg', 't00273.jpg', 't00391.jpg', 't00313.jpg', 't00240.jpg', 't00466.jpg',
                        't00539.jpg', 't00745.jpg', 't01067.jpg', 't00969.jpg', 't00740.jpg', 't00099.jpg',
                        't00574.jpg', 't00095.jpg', 't00143.jpg', 't00711.jpg', 't00727.jpg', 't00182.jpg',
                        't00173.jpg', 't00549.jpg', 't00946.jpg', 't00372.jpg', 't00518.jpg', 't00040.jpg',
                        't00754.jpg', 't00247.jpg', 't00028.jpg', 't00005.jpg', 't00689.jpg', 't00986.jpg',
                        't01126.jpg', 't01177.jpg', 't00900.jpg', 't00538.jpg', 't00120.jpg', 't00680.jpg',
                        't00350.jpg', 't00864.jpg', 't00652.jpg', 't00660.jpg', 't00733.jpg', 't00133.jpg',
                        't00636.jpg', 't00433.jpg', 't01163.jpg', 't00365.jpg', 't00412.jpg', 't00709.jpg',
                        't00000.jpg', 't00686.jpg', 't00953.jpg', 't00222.jpg', 't00718.jpg', 't00621.jpg',
                        't00501.jpg', 't00175.jpg', 't00051.jpg', 't00291.jpg', 't00771.jpg', 't00359.jpg',
                        't01165.jpg', 't00093.jpg', 't00203.jpg', 't00597.jpg', 't00507.jpg', 't00899.jpg',
                        't00635.jpg', 't00083.jpg', 't00186.jpg', 't00015.jpg', 't00532.jpg', 't00187.jpg',
                        't00772.jpg', 't00334.jpg', 't01005.jpg', 't00409.jpg', 't00315.jpg', 't00527.jpg',
                        't00006.jpg', 't00958.jpg', 't01147.jpg', 't00145.jpg', 't00819.jpg', 't00582.jpg',
                        't00565.jpg', 't01015.jpg', 't01082.jpg', 't01018.jpg', 't00178.jpg', 't00071.jpg',
                        't00159.jpg', 't00234.jpg', 't00394.jpg', 't00629.jpg', 't00948.jpg', 't00293.jpg',
                        't00436.jpg', 't00260.jpg', 't00923.jpg', 't00673.jpg', 't00687.jpg', 't00215.jpg',
                        't00166.jpg', 't00759.jpg', 't00619.jpg', 't00683.jpg', 't00218.jpg', 't00810.jpg',
                        't00191.jpg', 't00743.jpg', 't00561.jpg', 't01157.jpg', 't00677.jpg', 't00566.jpg',
                        't00788.jpg', 't01152.jpg', 't00871.jpg', 't00196.jpg', 't00939.jpg', 't00478.jpg',
                        't00949.jpg', 't00780.jpg', 't00341.jpg', 't00475.jpg', 't00590.jpg', 't00833.jpg',
                        't00888.jpg', 't00897.jpg', 't00576.jpg', 't00907.jpg', 't00626.jpg', 't00265.jpg',
                        't00932.jpg', 't00912.jpg', 't00317.jpg', 't00410.jpg', 't00973.jpg', 't00096.jpg',
                        't00227.jpg', 't00765.jpg', 't00995.jpg', 't00285.jpg', 't00584.jpg', 't00610.jpg',
                        't00972.jpg', 't00476.jpg', 't00058.jpg', 't00106.jpg']

    multiple_persons.sort()
    print("multiple_persons:", multiple_persons)

    # 2. 定义用于存储预测标签和预测结果的列表
    labels = []
    predicts = []

    # 3. 定义各个维度的得分列表
    language_score = []
    font_style_score = []
    rhetorical_devices_score = []
    syntactic_complexity_score = []
    figurative_language_score = []
    overall_score = []

    # 若你想统计 anaphoric_deictic_pronouns、abbreviated_names、multiple_persons 的平均得分，
    # 可以同样定义相应的列表
    anaphoric_deictic_score = []
    abbreviated_names_score = []
    multiple_persons_score = []

    # 4. 读取预测文件 generated_predictions.jsonl，每行一个 JSON
    with open("generated_predictions.jsonl", "r", encoding="utf-8") as file:
        prediction_lines = file.readlines()

    # 5. 提取标签和预测结果
    for line in prediction_lines:
        pred_data = json.loads(line)
        # 在 gold label 中搜索 txxx
        m = re.search(r"t\d+\b", pred_data["label"])
        if m:
            t_code = m.group(0)
        else:
            t_code = None

        # 替换预测中的 txxx
        if t_code:
            pred_data["predict"] = re.sub(r"t\d+\b", t_code, pred_data["predict"], count=1)
        labels.append(pred_data["label"])
        predicts.append(pred_data["predict"])

    # 6. 构造 gold_dict，用于后续对比
    gold_dict = {f"t{i:05d}": label for i, label in enumerate(labels)}

    # 7. 遍历预测结果，计算 Smatch 得分并分类汇总
    for i, predict in enumerate(predicts):
        try:
            idx = f"t{i:05d}"
            gold_penman = gold_dict[idx]

            # 在 gold label 中再次提取 txxx
            m_gold = re.search(r"\(t\d+\b", gold_penman)
            if m_gold:
                gold_t_code = m_gold.group(0)[1:]  # 去掉 "("
            else:
                gold_t_code = None

            # 计算 smatch
            pred_penman = predict

            # !!!!! for static
            # pred_penman = '''(t00294 / tombstone.n.01
            #         :ent (x1 / female.n.02
            #                            :rol (x2 / mother.n.01)
            #                            :nam "AALTJE VELDMAN"
            #                            :dob (x3 / date.n.05
            #                                                 :yoc "1852")
            #                  	     :dod (x4 / date.n.05
            #                                                 :yoc "1926")
            #                  	     :rol (x5 / widow.n.01
            #                                              :tgt (x6 / male.n.02
            #                                               :nam "HARM BORK"))))
            # '''

            (precision, recall, best_f_score), unmatched_1, unmatched_2 = score_amr_pairs(
                [gold_penman], [pred_penman]
            )

            # 存储 overall 分数
            overall_score.append(best_f_score)

            # 如果找到了 t_code，就根据文件名分类
            if gold_t_code:
                image_filename = f"{gold_t_code}.jpg"
                if image_filename in language_images:
                    language_score.append(best_f_score)
                if image_filename in font_style_images:
                    font_style_score.append(best_f_score)
                if image_filename in rhetorical_devices_images:
                    rhetorical_devices_score.append(best_f_score)
                if image_filename in syntactic_complexity_images:
                    syntactic_complexity_score.append(best_f_score)
                if image_filename in figurative_language_images:
                    figurative_language_score.append(best_f_score)

                # 若需要对 anaphoric_deictic_pronouns 等进行统计，也可类似添加
                if image_filename in anaphoric_deictic_pronouns:
                    anaphoric_deictic_score.append(best_f_score)
                if image_filename in abbreviated_names:
                    abbreviated_names_score.append(best_f_score)
                if image_filename in multiple_persons:
                    multiple_persons_score.append(best_f_score)

        except Exception as e:
            print(f"Error processing {idx}: {e}")

    # 8. 计算并打印各维度的平均得分
    # overall
    if overall_score:
        print(f"Average overall score: {sum(overall_score) / len(overall_score):.3f}")
    else:
        print("No overall scores calculated.")

    # language
    if language_score:
        print(f"Average score on language: {sum(language_score) / len(language_images):.3f}")
    else:
        print("No scores for language.")

    # font_style
    if font_style_score:
        print(f"Average score on font style: {sum(font_style_score) / len(font_style_images):.3f}")
    else:
        print("No scores for font style.")

    # rhetorical_devices
    if rhetorical_devices_score:
        print(
            f"Average score on rhetorical devices: {sum(rhetorical_devices_score) / len(rhetorical_devices_images):.3f}")
    else:
        print("No scores for rhetorical devices.")

    # syntactic_complexity
    if syntactic_complexity_score:
        print(
            f"Average score on syntactic complexity: {sum(syntactic_complexity_score) / len(syntactic_complexity_images):.3f}")
    else:
        print("No scores for syntactic complexity.")

    # figurative_language
    if figurative_language_score:
        print(
            f"Average score on figurative language: {sum(figurative_language_score) / len(figurative_language_images):.3f}")
    else:
        print("No scores for figurative language.")

    # 如果需要，也可输出 anaphoric_deictic_score 等
    if anaphoric_deictic_score:
        print(
            f"Average score on anaphoric_deictic_pronouns: {sum(anaphoric_deictic_score) / len(anaphoric_deictic_pronouns):.3f}")
    else:
        print("No scores for anaphoric_deictic_pronouns.")

    if abbreviated_names_score:
        print(f"Average score on abbreviated_names: {sum(abbreviated_names_score) / len(abbreviated_names):.3f}")
    else:
        print("No scores for abbreviated_names.")

    if multiple_persons_score:
        print(f"Average score on multiple_persons: {sum(multiple_persons_score) / len(multiple_persons):.3f}")
    else:
        print("No scores for multiple_persons.")
