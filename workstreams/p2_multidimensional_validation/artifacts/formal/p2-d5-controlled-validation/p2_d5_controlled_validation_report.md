# Formal coefficient analysis, d=5

## EMPIRICAL numerical outcomes

All numerical tables below are simulation outcomes, not proven statements.

Source commit: `85e97fa34e23084410c148b63d814c75d92dbc1e`

Config SHA-256: `d3371a99a0f7f67140937c0b5eda9a94b2aa431338ebf8561988ddd995ac6d4e`

Matrix: `p2-d5-controlled-validation`

## Frozen inputs

Theory: `{"B11_d": [-0.007741472935786256, -0.02515889035292379, 0.01773415031499783, -0.01876602841108497, 0.00880723010440575], "B11_d_sign_is_intrinsic": true, "S_C": [[0.35416473352098043, 0.02779582047084913, 0.01806310274307949, -0.0014569479115977557, 0.000122751340053028], [0.02779582047084913, 0.3495905627898378, 0.01101626317972773, 0.014117526532011666, -0.001186982554662978], [0.01806310274307949, 0.01101626317972773, 0.4049209090598549, 0.03265048452592303, 0.012196223305747204], [-0.0014569479115977557, 0.014117526532011666, 0.03265048452592303, 0.28476945183498037, 0.01918330202416588], [0.000122751340053028, -0.001186982554662978, 0.012196223305747204, 0.01918330202416588, 0.39846533583806676]], "by_H": {"2": {"B20": [-0.014024998786462132, -0.04557962155204393, 0.03212843843928615, -0.03399786163115589, 0.015955799697419393], "B20_ctrl": [-0.004674999595487377, -0.015193207184014642, 0.01070947947976205, -0.011332620543718629, 0.005318599899139798], "B20_local": [-0.009349999190974755, -0.030386414368029285, 0.0214189589595241, -0.022665241087437258, 0.010637199798279595]}, "4": {"B20": [-0.04441249615713008, -0.14433546824813875, 0.10174005505773948, -0.10765989516532698, 0.050526699041827994], "B20_ctrl": [-0.01636249858420582, -0.05317622514405063, 0.03748317817916719, -0.0396641719030152, 0.018615099646989278], "B20_local": [-0.02804999757292426, -0.09115924310408786, 0.0642568768785723, -0.06799572326231178, 0.031911599394838785]}}, "normalization": "C_hat = (b_hat - (gamma / N) * B11_d) / gamma^2", "remainder": "O(1/N + gamma)"}`

Setting matrix: `{"H_values": [2, 4], "N_values": [32, 48, 64, 96, 128], "all_unique": true, "chains": 80, "chains_per_setting": [8, 8, 8, 8, 8, 8, 8, 8, 8, 8], "gamma_equals_inverse_N": true, "matrix_id": "p2-d5-controlled-validation", "seeds": [1201, 1202, 1203, 1204, 1205, 1206, 1207, 1208], "settings": 10, "target": "d5", "unique_run_ids": 80}`

Seed block: `[1201, 1202, 1203, 1204, 1205, 1206, 1207, 1208]`

Primary estimator: signed coordinatewise stationary mean-balance. The direct stationary sample mean remains diagnostic.

Stopping protocol: `{"absolute_half_width": 0.0025, "check_after_batches": 100, "coordinate_rule": "h_j <= max(0.0025, 0.10 * abs(B20_j(H)))", "extend_by_batches": 50, "relative_half_width": 0.1, "scope": "every_coordinate", "simultaneous_interval": "bonferroni_familywise_95_percent", "statistic": "primary_balance_normalized_coefficient", "stop_at_batches": 400, "stop_on_invalidity": true}`

Uncertainty: `{"coordinates": 5, "correction": "bonferroni", "degrees_of_freedom": 7, "familywise_confidence_level": 0.95, "marginal_diagnostic_confidence_level": 0.95, "method": "student_t_coordinatewise", "pool_coordinates": false, "simultaneous_coordinate_confidence_level": 0.99, "simultaneous_t_critical": 3.4994832973504924, "source": "eight_independent_chain_estimates"}`

Fit: `{"coefficient_estimate": "beta0_j", "delta": "gamma + 1/N", "model": "C_hat_j = beta0_j + beta1_j * delta", "per": ["H", "coordinate"], "response": "setting_mean_balance_C_hat_coordinate", "settings_per_fit": 5}`

Bootstrap: `{"correction": "bonferroni", "marginal_diagnostic_percentile_level": 0.95, "marginal_diagnostic_quantiles": [0.025, 0.975], "preserve_same_seed_across_settings": true, "repetitions": 5000, "seed": 3901, "simultaneous_coordinate_percentile_level": 0.99, "simultaneous_familywise_confidence_level": 0.95, "simultaneous_quantiles": [0.005, 0.995], "unit": "seed_label_block"}`

## Coordinatewise settings

| H | N | gamma | delta | coordinate | estimator | C_mean | simultaneous_ci_low | simultaneous_ci_high | B20_component |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 32 | 0.03125 | 0.0625 | 0 | direct_sample_mean | -0.0888314392 | -0.828805922 | 0.651143043 | -0.0140249988 |
| 2 | 32 | 0.03125 | 0.0625 | 1 | direct_sample_mean | -0.0480035156 | -0.650366081 | 0.55435905 | -0.0455796216 |
| 2 | 32 | 0.03125 | 0.0625 | 2 | direct_sample_mean | -0.0517384714 | -0.678114596 | 0.574637653 | 0.0321284384 |
| 2 | 32 | 0.03125 | 0.0625 | 3 | direct_sample_mean | -0.00687148529 | -0.389029564 | 0.375286593 | -0.0339978616 |
| 2 | 32 | 0.03125 | 0.0625 | 4 | direct_sample_mean | -0.0899491864 | -0.64580334 | 0.465904967 | 0.0159557997 |
| 2 | 32 | 0.03125 | 0.0625 | 0 | stationary_mean_balance | -0.0139084983 | -0.0142508726 | -0.0135661239 | -0.0140249988 |
| 2 | 32 | 0.03125 | 0.0625 | 1 | stationary_mean_balance | -0.0446868622 | -0.0458000272 | -0.0435736973 | -0.0455796216 |
| 2 | 32 | 0.03125 | 0.0625 | 2 | stationary_mean_balance | 0.0313306603 | 0.0305458458 | 0.0321154748 | 0.0321284384 |
| 2 | 32 | 0.03125 | 0.0625 | 3 | stationary_mean_balance | -0.0333351747 | -0.0341654819 | -0.0325048674 | -0.0339978616 |
| 2 | 32 | 0.03125 | 0.0625 | 4 | stationary_mean_balance | 0.0155611153 | 0.0151713579 | 0.0159508726 | 0.0159557997 |
| 2 | 48 | 0.0208333333 | 0.0416666667 | 0 | direct_sample_mean | 0.202600394 | -0.720093364 | 1.12529415 | -0.0140249988 |
| 2 | 48 | 0.0208333333 | 0.0416666667 | 1 | direct_sample_mean | 0.207000045 | -0.663142737 | 1.07714283 | -0.0455796216 |
| 2 | 48 | 0.0208333333 | 0.0416666667 | 2 | direct_sample_mean | 0.318304224 | -0.392766753 | 1.0293752 | 0.0321284384 |
| 2 | 48 | 0.0208333333 | 0.0416666667 | 3 | direct_sample_mean | 0.0873714728 | -0.488531389 | 0.663274335 | -0.0339978616 |
| 2 | 48 | 0.0208333333 | 0.0416666667 | 4 | direct_sample_mean | -0.177065914 | -0.89132207 | 0.537190242 | 0.0159557997 |
| 2 | 48 | 0.0208333333 | 0.0416666667 | 0 | stationary_mean_balance | -0.0140038681 | -0.0142590457 | -0.0137486906 | -0.0140249988 |
| 2 | 48 | 0.0208333333 | 0.0416666667 | 1 | stationary_mean_balance | -0.0451676814 | -0.0459971594 | -0.0443382034 | -0.0455796216 |
| 2 | 48 | 0.0208333333 | 0.0416666667 | 2 | stationary_mean_balance | 0.031725562 | 0.0311408154 | 0.0323103086 | 0.0321284384 |
| 2 | 48 | 0.0208333333 | 0.0416666667 | 3 | stationary_mean_balance | -0.0336927808 | -0.0343114876 | -0.0330740739 | -0.0339978616 |
| 2 | 48 | 0.0208333333 | 0.0416666667 | 4 | stationary_mean_balance | 0.0157567028 | 0.0154663033 | 0.0160471024 | 0.0159557997 |
| 2 | 64 | 0.015625 | 0.03125 | 0 | direct_sample_mean | -0.0319872056 | -1.04205594 | 0.978081533 | -0.0140249988 |
| 2 | 64 | 0.015625 | 0.03125 | 1 | direct_sample_mean | 0.51165958 | -0.554761349 | 1.57808051 | -0.0455796216 |
| 2 | 64 | 0.015625 | 0.03125 | 2 | direct_sample_mean | 0.628222448 | -0.354168858 | 1.61061375 | 0.0321284384 |
| 2 | 64 | 0.015625 | 0.03125 | 3 | direct_sample_mean | 0.0526738369 | -1.0421807 | 1.14752837 | -0.0339978616 |
| 2 | 64 | 0.015625 | 0.03125 | 4 | direct_sample_mean | -0.105649997 | -1.08327605 | 0.871976057 | 0.0159557997 |
| 2 | 64 | 0.015625 | 0.03125 | 0 | stationary_mean_balance | -0.0140650972 | -0.014272484 | -0.0138577105 | -0.0140249988 |
| 2 | 64 | 0.015625 | 0.03125 | 1 | stationary_mean_balance | -0.0454522973 | -0.0461263014 | -0.0447782933 | -0.0455796216 |
| 2 | 64 | 0.015625 | 0.03125 | 2 | stationary_mean_balance | 0.0319542419 | 0.0314791389 | 0.0324293449 | 0.0321284384 |
| 2 | 64 | 0.015625 | 0.03125 | 3 | stationary_mean_balance | -0.0339045433 | -0.0344072831 | -0.0334018035 | -0.0339978616 |
| 2 | 64 | 0.015625 | 0.03125 | 4 | stationary_mean_balance | 0.0158700158 | 0.0156340676 | 0.016105964 | 0.0159557997 |
| 2 | 96 | 0.0104166667 | 0.0208333333 | 0 | direct_sample_mean | 0.361250628 | -1.63443776 | 2.35693901 | -0.0140249988 |
| 2 | 96 | 0.0104166667 | 0.0208333333 | 1 | direct_sample_mean | 1.32982212 | 0.16233379 | 2.49731046 | -0.0455796216 |
| 2 | 96 | 0.0104166667 | 0.0208333333 | 2 | direct_sample_mean | 0.207864566 | -1.68985654 | 2.10558567 | 0.0321284384 |
| 2 | 96 | 0.0104166667 | 0.0208333333 | 3 | direct_sample_mean | 0.0371338781 | -1.8417983 | 1.91606606 | -0.0339978616 |
| 2 | 96 | 0.0104166667 | 0.0208333333 | 4 | direct_sample_mean | 0.0571440891 | -2.65351916 | 2.76780734 | 0.0159557997 |
| 2 | 96 | 0.0104166667 | 0.0208333333 | 0 | stationary_mean_balance | -0.0139982072 | -0.0142690975 | -0.013727317 | -0.0140249988 |
| 2 | 96 | 0.0104166667 | 0.0208333333 | 1 | stationary_mean_balance | -0.0453205671 | -0.0462008636 | -0.0444402707 | -0.0455796216 |
| 2 | 96 | 0.0104166667 | 0.0208333333 | 2 | stationary_mean_balance | 0.0318894581 | 0.031268971 | 0.0325099453 | 0.0321284384 |
| 2 | 96 | 0.0104166667 | 0.0208333333 | 3 | stationary_mean_balance | -0.0338057445 | -0.0344623585 | -0.0331491305 | -0.0339978616 |
| 2 | 96 | 0.0104166667 | 0.0208333333 | 4 | stationary_mean_balance | 0.0158375941 | 0.0155294442 | 0.016145744 | 0.0159557997 |
| 2 | 128 | 0.0078125 | 0.015625 | 0 | direct_sample_mean | 1.60160088 | -0.864683427 | 4.06788518 | -0.0140249988 |
| 2 | 128 | 0.0078125 | 0.015625 | 1 | direct_sample_mean | 1.31755533 | -0.107815918 | 2.74292658 | -0.0455796216 |
| 2 | 128 | 0.0078125 | 0.015625 | 2 | direct_sample_mean | 0.0328977921 | -2.845249 | 2.91104458 | 0.0321284384 |
| 2 | 128 | 0.0078125 | 0.015625 | 3 | direct_sample_mean | -0.0523170222 | -2.14193095 | 2.03729691 | -0.0339978616 |
| 2 | 128 | 0.0078125 | 0.015625 | 4 | direct_sample_mean | -0.310042631 | -2.37908576 | 1.7590005 | 0.0159557997 |
| 2 | 128 | 0.0078125 | 0.015625 | 0 | stationary_mean_balance | -0.0140044306 | -0.0143226326 | -0.0136862286 | -0.0140249988 |
| 2 | 128 | 0.0078125 | 0.015625 | 1 | stationary_mean_balance | -0.0453837375 | -0.0464178801 | -0.0443495948 | -0.0455796216 |
| 2 | 128 | 0.0078125 | 0.015625 | 2 | stationary_mean_balance | 0.0319480618 | 0.0312191015 | 0.032677022 | 0.0321284384 |
| 2 | 128 | 0.0078125 | 0.015625 | 3 | stationary_mean_balance | -0.0338525888 | -0.0346239562 | -0.0330812215 | -0.0339978616 |
| 2 | 128 | 0.0078125 | 0.015625 | 4 | stationary_mean_balance | 0.0158665762 | 0.015504556 | 0.0162285963 | 0.0159557997 |
| 4 | 32 | 0.03125 | 0.0625 | 0 | direct_sample_mean | -0.114987672 | -0.867226499 | 0.637251156 | -0.0444124962 |
| 4 | 32 | 0.03125 | 0.0625 | 1 | direct_sample_mean | -0.140794748 | -0.766003227 | 0.484413731 | -0.144335468 |
| 4 | 32 | 0.03125 | 0.0625 | 2 | direct_sample_mean | 0.0105976847 | -0.619755344 | 0.640950714 | 0.101740055 |
| 4 | 32 | 0.03125 | 0.0625 | 3 | direct_sample_mean | -0.0608682535 | -0.448077669 | 0.326341162 | -0.107659895 |
| 4 | 32 | 0.03125 | 0.0625 | 4 | direct_sample_mean | -0.0439418239 | -0.603334647 | 0.515450999 | 0.050526699 |
| 4 | 32 | 0.03125 | 0.0625 | 0 | stationary_mean_balance | -0.0412461148 | -0.0415730876 | -0.040919142 | -0.0444124962 |
| 4 | 32 | 0.03125 | 0.0625 | 1 | stationary_mean_balance | -0.131363811 | -0.132427335 | -0.130300288 | -0.144335468 |
| 4 | 32 | 0.03125 | 0.0625 | 2 | stationary_mean_balance | 0.091717877 | 0.0909679132 | 0.0924678408 | 0.101740055 |
| 4 | 32 | 0.03125 | 0.0625 | 3 | stationary_mean_balance | -0.0980011119 | -0.0987943887 | -0.097207835 | -0.107659895 |
| 4 | 32 | 0.03125 | 0.0625 | 4 | stationary_mean_balance | 0.0455573416 | 0.045184893 | 0.0459297901 | 0.050526699 |
| 4 | 48 | 0.0208333333 | 0.0416666667 | 0 | direct_sample_mean | 0.17923002 | -0.74343468 | 1.10189472 | -0.0444124962 |
| 4 | 48 | 0.0208333333 | 0.0416666667 | 1 | direct_sample_mean | 0.114419463 | -0.753144444 | 0.981983371 | -0.144335468 |
| 4 | 48 | 0.0208333333 | 0.0416666667 | 2 | direct_sample_mean | 0.378678763 | -0.337800287 | 1.09515781 | 0.101740055 |
| 4 | 48 | 0.0208333333 | 0.0416666667 | 3 | direct_sample_mean | 0.028440232 | -0.544072928 | 0.600953392 | -0.107659895 |
| 4 | 48 | 0.0208333333 | 0.0416666667 | 4 | direct_sample_mean | -0.132579391 | -0.85018509 | 0.585026308 | 0.050526699 |
| 4 | 48 | 0.0208333333 | 0.0416666667 | 0 | stationary_mean_balance | -0.04232947 | -0.0425708761 | -0.0420880638 | -0.0444124962 |
| 4 | 48 | 0.0208333333 | 0.0416666667 | 1 | stationary_mean_balance | -0.135706402 | -0.136491407 | -0.134921397 | -0.144335468 |
| 4 | 48 | 0.0208333333 | 0.0416666667 | 2 | stationary_mean_balance | 0.0950481187 | 0.0944946251 | 0.0956016123 | 0.101740055 |
| 4 | 48 | 0.0208333333 | 0.0416666667 | 3 | stationary_mean_balance | -0.101235288 | -0.10182082 | -0.100649755 | -0.107659895 |
| 4 | 48 | 0.0208333333 | 0.0416666667 | 4 | stationary_mean_balance | 0.0472086506 | 0.0469337729 | 0.0474835283 | 0.050526699 |
| 4 | 64 | 0.015625 | 0.03125 | 0 | direct_sample_mean | -0.0496936044 | -1.04418851 | 0.944801298 | -0.0444124962 |
| 4 | 64 | 0.015625 | 0.03125 | 1 | direct_sample_mean | 0.431934095 | -0.640867844 | 1.50473603 | -0.144335468 |
| 4 | 64 | 0.015625 | 0.03125 | 2 | direct_sample_mean | 0.689719942 | -0.283470154 | 1.66291004 | 0.101740055 |
| 4 | 64 | 0.015625 | 0.03125 | 3 | direct_sample_mean | -0.0246716853 | -1.10195788 | 1.05261451 | -0.107659895 |
| 4 | 64 | 0.015625 | 0.03125 | 4 | direct_sample_mean | -0.0679043089 | -1.05520846 | 0.919399841 | 0.050526699 |
| 4 | 64 | 0.015625 | 0.03125 | 0 | stationary_mean_balance | -0.0428839875 | -0.043085776 | -0.0426821989 | -0.0444124962 |
| 4 | 64 | 0.015625 | 0.03125 | 1 | stationary_mean_balance | -0.137946242 | -0.138602011 | -0.137290474 | -0.144335468 |
| 4 | 64 | 0.015625 | 0.03125 | 2 | stationary_mean_balance | 0.0967703744 | 0.0963081377 | 0.097232611 | 0.101740055 |
| 4 | 64 | 0.015625 | 0.03125 | 3 | stationary_mean_balance | -0.102903274 | -0.103392413 | -0.102414136 | -0.107659895 |
| 4 | 64 | 0.015625 | 0.03125 | 4 | stationary_mean_balance | 0.0480626513 | 0.0478330928 | 0.0482922098 | 0.050526699 |
| 4 | 96 | 0.0104166667 | 0.0208333333 | 0 | direct_sample_mean | 0.334912069 | -1.65807356 | 2.3278977 | -0.0444124962 |
| 4 | 96 | 0.0104166667 | 0.0208333333 | 1 | direct_sample_mean | 1.23110479 | 0.0638652463 | 2.39834434 | -0.144335468 |
| 4 | 96 | 0.0104166667 | 0.0208333333 | 2 | direct_sample_mean | 0.273471289 | -1.61879803 | 2.1657406 | 0.101740055 |
| 4 | 96 | 0.0104166667 | 0.0208333333 | 3 | direct_sample_mean | -0.0211485641 | -1.89997086 | 1.85767373 | -0.107659895 |
| 4 | 96 | 0.0104166667 | 0.0208333333 | 4 | direct_sample_mean | 0.091783172 | -2.63286928 | 2.81643563 | 0.050526699 |
| 4 | 96 | 0.0104166667 | 0.0208333333 | 0 | stationary_mean_balance | -0.0433287589 | -0.0436108123 | -0.0430467055 | -0.0444124962 |
| 4 | 96 | 0.0104166667 | 0.0208333333 | 1 | stationary_mean_balance | -0.139846862 | -0.140762966 | -0.138930758 | -0.144335468 |
| 4 | 96 | 0.0104166667 | 0.0208333333 | 2 | stationary_mean_balance | 0.0982592576 | 0.0976136845 | 0.0989048307 | 0.101740055 |
| 4 | 96 | 0.0104166667 | 0.0208333333 | 3 | stationary_mean_balance | -0.104318081 | -0.105001407 | -0.103634755 | -0.107659895 |
| 4 | 96 | 0.0104166667 | 0.0208333333 | 4 | stationary_mean_balance | 0.0488007401 | 0.0484801306 | 0.0491213497 | 0.050526699 |
| 4 | 128 | 0.0078125 | 0.015625 | 0 | direct_sample_mean | 1.56061101 | -0.905311606 | 4.02653362 | -0.0444124962 |
| 4 | 128 | 0.0078125 | 0.015625 | 1 | direct_sample_mean | 1.20553734 | -0.20656574 | 2.61764042 | -0.144335468 |
| 4 | 128 | 0.0078125 | 0.015625 | 2 | direct_sample_mean | 0.0810106267 | -2.81170393 | 2.97372518 | 0.101740055 |
| 4 | 128 | 0.0078125 | 0.015625 | 3 | direct_sample_mean | -0.124271228 | -2.20524717 | 1.95670472 | -0.107659895 |
| 4 | 128 | 0.0078125 | 0.015625 | 4 | direct_sample_mean | -0.275649882 | -2.33620903 | 1.78490926 | 0.050526699 |
| 4 | 128 | 0.0078125 | 0.015625 | 0 | stationary_mean_balance | -0.0436020582 | -0.0439262954 | -0.0432778211 | -0.0444124962 |
| 4 | 128 | 0.0078125 | 0.015625 | 1 | stationary_mean_balance | -0.140969427 | -0.142023068 | -0.139915785 | -0.144335468 |
| 4 | 128 | 0.0078125 | 0.015625 | 2 | stationary_mean_balance | 0.0991273547 | 0.0983846873 | 0.0998700221 | 0.101740055 |
| 4 | 128 | 0.0078125 | 0.015625 | 3 | stationary_mean_balance | -0.105153909 | -0.105939821 | -0.104367996 | -0.107659895 |
| 4 | 128 | 0.0078125 | 0.015625 | 4 | stationary_mean_balance | 0.0492311904 | 0.0488623626 | 0.0496000182 | 0.050526699 |

## Extrapolated intercepts

| H | coordinate | beta0 | beta1 | simultaneous_ci_low | simultaneous_ci_high | B20_component | intercept_theory_error | theory_covered_simultaneous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 0 | -0.0140655061 | 0.00202140516 | -0.01427098 | -0.0138295249 | -0.0140249988 | -4.05073083e-05 | True |
| 2 | 1 | -0.0457104417 | 0.0147843674 | -0.0463785328 | -0.0449434842 | -0.0455796216 | -0.000130820187 | True |
| 2 | 2 | 0.032220357 | -0.0131130237 | 0.0316797243 | 0.0326913914 | 0.0321284384 | 9.19185752e-05 | True |
| 2 | 3 | -0.0340954937 | 0.0109767949 | -0.0345938212 | -0.0335234201 | -0.0339978616 | -9.76321093e-05 | True |
| 2 | 4 | 0.0160014114 | -0.00648758189 | 0.0157329196 | 0.0162353381 | 0.0159557997 | 4.56117524e-05 | True |
| 4 | 0 | -0.0444005615 | 0.0501086145 | -0.0446094313 | -0.0441636371 | -0.0444124962 | 1.19346609e-05 | True |
| 4 | 1 | -0.14419271 | 0.204397413 | -0.144872478 | -0.14342241 | -0.144335468 | 0.000142758311 | True |
| 4 | 2 | 0.101605216 | -0.15769076 | 0.101062137 | 0.102084693 | 0.101740055 | -0.000134838715 | True |
| 4 | 3 | -0.107554333 | 0.152203652 | -0.108061367 | -0.106979768 | -0.107659895 | 0.00010556176 | True |
| 4 | 4 | 0.050459816 | -0.0781876699 | 0.0501901098 | 0.0506979332 | 0.050526699 | -6.6883076e-05 | True |

## Frozen V0–V5 gates

| gate | scope | passed | detail |
| --- | --- | --- | --- |
| V0 | all_settings | True | finite_control_stationarity_and_validated_matrix |
| V1 | H2_all_five_coordinates | True | all_coordinate_simultaneous_bootstrap_coverage |
| V2 | H4_all_five_coordinates | True | all_coordinate_simultaneous_bootstrap_coverage |
| V3 | p2-d5-controlled-validation__H2__N32__g0p0312500000__coordinate_0 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N32__g0p0312500000__coordinate_1 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N32__g0p0312500000__coordinate_2 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N32__g0p0312500000__coordinate_3 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N32__g0p0312500000__coordinate_4 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N48__g0p0208333333__coordinate_0 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N48__g0p0208333333__coordinate_1 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N48__g0p0208333333__coordinate_2 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N48__g0p0208333333__coordinate_3 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N48__g0p0208333333__coordinate_4 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N64__g0p0156250000__coordinate_0 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N64__g0p0156250000__coordinate_1 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N64__g0p0156250000__coordinate_2 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N64__g0p0156250000__coordinate_3 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N64__g0p0156250000__coordinate_4 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N96__g0p0104166667__coordinate_0 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N96__g0p0104166667__coordinate_1 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N96__g0p0104166667__coordinate_2 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N96__g0p0104166667__coordinate_3 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N96__g0p0104166667__coordinate_4 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N128__g0p0078125000__coordinate_0 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N128__g0p0078125000__coordinate_1 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N128__g0p0078125000__coordinate_2 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N128__g0p0078125000__coordinate_3 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H2__N128__g0p0078125000__coordinate_4 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N32__g0p0312500000__coordinate_0 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N32__g0p0312500000__coordinate_1 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N32__g0p0312500000__coordinate_2 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N32__g0p0312500000__coordinate_3 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N32__g0p0312500000__coordinate_4 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N48__g0p0208333333__coordinate_0 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N48__g0p0208333333__coordinate_1 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N48__g0p0208333333__coordinate_2 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N48__g0p0208333333__coordinate_3 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N48__g0p0208333333__coordinate_4 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N64__g0p0156250000__coordinate_0 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N64__g0p0156250000__coordinate_1 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N64__g0p0156250000__coordinate_2 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N64__g0p0156250000__coordinate_3 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N64__g0p0156250000__coordinate_4 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N96__g0p0104166667__coordinate_0 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N96__g0p0104166667__coordinate_1 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N96__g0p0104166667__coordinate_2 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N96__g0p0104166667__coordinate_3 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N96__g0p0104166667__coordinate_4 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N128__g0p0078125000__coordinate_0 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N128__g0p0078125000__coordinate_1 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N128__g0p0078125000__coordinate_2 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N128__g0p0078125000__coordinate_3 |  | diagnostic_only_setting_sign |
| V3 | p2-d5-controlled-validation__H4__N128__g0p0078125000__coordinate_4 |  | diagnostic_only_setting_sign |
| V4 | p2-d5-controlled-validation__H2__N32__g0p0312500000__coordinate_0 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N32__g0p0312500000__coordinate_1 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N32__g0p0312500000__coordinate_2 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N32__g0p0312500000__coordinate_3 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N32__g0p0312500000__coordinate_4 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N48__g0p0208333333__coordinate_0 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N48__g0p0208333333__coordinate_1 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N48__g0p0208333333__coordinate_2 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N48__g0p0208333333__coordinate_3 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N48__g0p0208333333__coordinate_4 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N64__g0p0156250000__coordinate_0 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N64__g0p0156250000__coordinate_1 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N64__g0p0156250000__coordinate_2 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N64__g0p0156250000__coordinate_3 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N64__g0p0156250000__coordinate_4 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N96__g0p0104166667__coordinate_0 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N96__g0p0104166667__coordinate_1 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N96__g0p0104166667__coordinate_2 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N96__g0p0104166667__coordinate_3 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N96__g0p0104166667__coordinate_4 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N128__g0p0078125000__coordinate_0 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N128__g0p0078125000__coordinate_1 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N128__g0p0078125000__coordinate_2 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N128__g0p0078125000__coordinate_3 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H2__N128__g0p0078125000__coordinate_4 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N32__g0p0312500000__coordinate_0 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N32__g0p0312500000__coordinate_1 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N32__g0p0312500000__coordinate_2 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N32__g0p0312500000__coordinate_3 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N32__g0p0312500000__coordinate_4 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N48__g0p0208333333__coordinate_0 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N48__g0p0208333333__coordinate_1 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N48__g0p0208333333__coordinate_2 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N48__g0p0208333333__coordinate_3 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N48__g0p0208333333__coordinate_4 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N64__g0p0156250000__coordinate_0 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N64__g0p0156250000__coordinate_1 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N64__g0p0156250000__coordinate_2 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N64__g0p0156250000__coordinate_3 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N64__g0p0156250000__coordinate_4 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N96__g0p0104166667__coordinate_0 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N96__g0p0104166667__coordinate_1 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N96__g0p0104166667__coordinate_2 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N96__g0p0104166667__coordinate_3 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N96__g0p0104166667__coordinate_4 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N128__g0p0078125000__coordinate_0 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N128__g0p0078125000__coordinate_1 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N128__g0p0078125000__coordinate_2 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N128__g0p0078125000__coordinate_3 |  | diagnostic_only_direct_minus_balance |
| V4 | p2-d5-controlled-validation__H4__N128__g0p0078125000__coordinate_4 |  | diagnostic_only_direct_minus_balance |
| V5 | frozen_matrix | True | exactly_ten_settings_and_eighty_chains |

## Interpretation boundary

The pre-registered controlled d=5 experiment is consistent with the multidimensional higher-order coefficient for H=2 and H=4 under the frozen coordinatewise simultaneous-bootstrap criterion. This does not establish a theorem, arbitrary-dimensional validity, d=5 FedAvg attribution, separate empirical identification of local/control terms, heterogeneity, state-dependent noise, or growing H.

Manifest: `p2-d5-controlled-validation`
