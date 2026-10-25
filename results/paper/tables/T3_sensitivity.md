| group                 | case              | overrides                               |   co2_kt |   fuel_MSm3 |   gt_low_load_unit_hours |   lost_production_pct |   wind_curtailed_GWh |
|:----------------------|:------------------|:----------------------------------------|---------:|------------:|-------------------------:|----------------------:|---------------------:|
| wind_farm_size        | wind_fixed        | {'n_turbines': 1}                       |    77.55 |       33.14 |                     9062 |             0         |              0       |
| wind_farm_size        | wind_fixed        | {'n_turbines': 2}                       |    64.66 |       27.63 |                     9005 |             0         |             44.49    |
| wind_farm_size        | wind_fixed        | {'n_turbines': 3}                       |    60.23 |       25.74 |                     9085 |             0         |            103.9     |
| wind_farm_size        | wind_fixed        | {'n_turbines': 4}                       |    57.56 |       24.6  |                     9114 |             0         |            166.2     |
| wind_farm_size        | wind_flex         | {'n_turbines': 1}                       |    72.04 |       30.79 |                     4658 |             0         |              0.07779 |
| wind_farm_size        | wind_flex         | {'n_turbines': 2}                       |    57.55 |       24.59 |                     5928 |             0         |             38.76    |
| wind_farm_size        | wind_flex         | {'n_turbines': 3}                       |    53.34 |       22.8  |                     6575 |             0         |             97.39    |
| wind_farm_size        | wind_flex         | {'n_turbines': 4}                       |    50.92 |       21.76 |                     6910 |             0         |            159.5     |
| co2_price             | wind_flex         | {'co2_price': 0.5}                      |    57.5  |       24.57 |                     5926 |             0         |             38.68    |
| co2_price             | wind_flex         | {'co2_price': 1.0}                      |    57.51 |       24.57 |                     5943 |             0         |             38.69    |
| co2_price             | wind_flex         | {'co2_price': 2.0}                      |    57.55 |       24.59 |                     5928 |             0         |             38.76    |
| co2_price             | wind_flex         | {'co2_price': 3.0}                      |    57.49 |       24.57 |                     5922 |             0         |             38.71    |
| gas_price             | wind_flex         | {'gas_price': 2.0}                      |    57.53 |       24.58 |                     5906 |             2.83e-05  |             38.76    |
| gas_price             | wind_flex         | {'gas_price': 4.19}                     |    57.55 |       24.59 |                     5928 |             0         |             38.76    |
| gas_price             | wind_flex         | {'gas_price': 8.0}                      |    57.49 |       24.57 |                     5942 |             0         |             38.71    |
| battery_size          | wind_flex_battery | {'battery': [0, 0]}                     |    57.55 |       24.59 |                     5928 |             0         |             38.76    |
| battery_size          | wind_flex_battery | {'battery': [2, 2]}                     |    57.32 |       24.5  |                     6101 |             0         |             38.43    |
| battery_size          | wind_flex_battery | {'battery': [4, 4]}                     |    57.15 |       24.42 |                     6235 |             0         |             38.04    |
| battery_size          | wind_flex_battery | {'battery': [8, 8]}                     |    56.87 |       24.3  |                     6258 |             0         |             37.42    |
| battery_size          | wind_flex_battery | {'battery': [8, 16]}                    |    56.43 |       24.11 |                     6363 |             0         |             36.48    |
| injection_deficit     | wind_flex         | {'max_deficit': 0}                      |    64.65 |       27.63 |                     8993 |             0.0002022 |             44.49    |
| injection_deficit     | wind_flex         | {'max_deficit': 24}                     |    57.55 |       24.59 |                     5937 |             0         |             38.74    |
| injection_deficit     | wind_flex         | {'max_deficit': 72}                     |    57.55 |       24.59 |                     5928 |             0         |             38.76    |
| injection_deficit     | wind_flex         | {'max_deficit': 168}                    |    57.5  |       24.57 |                     5930 |             0         |             38.68    |
| min_gt_online         | wind_flex_battery | {'min_gt_online': 1, 'battery': [8, 8]} |    56.87 |       24.3  |                     6258 |             0         |             37.42    |
| min_gt_online         | wind_flex_battery | {'min_gt_online': 0, 'battery': [8, 8]} |    38.68 |       16.53 |                      854 |             0         |             10.96    |
| gt_fleet              | wind_flex         | {'fleet': {'main': 3}}                  |    57.55 |       24.59 |                     5928 |             0         |             38.76    |
| gt_fleet              | wind_flex         | {'fleet': {'main': 2, 'small': 1}}      |    55.61 |       23.77 |                     5809 |             0         |             36.86    |
| gt_operation_practice | wind_fixed        | {'min_gt_online': 2}                    |    90.74 |       38.78 |                    17520 |             0         |             61.09    |
| gt_operation_practice | wind_flex         | {'min_gt_online': 2}                    |    87.68 |       37.47 |                    17520 |             0         |             55.08    |