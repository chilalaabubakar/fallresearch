| group                 | case              | overrides                               |   co2_kt |   fuel_MSm3 |   gt_low_load_unit_hours |   lost_production_pct |   wind_curtailed_GWh |
|:----------------------|:------------------|:----------------------------------------|---------:|------------:|-------------------------:|----------------------:|---------------------:|
| wind_farm_size        | wind_fixed        | {'n_turbines': 1}                       |    71.74 |       36.89 |                     6911 |                     0 |                0.457 |
| wind_farm_size        | wind_fixed        | {'n_turbines': 2}                       |    60.7  |       31.22 |                     7176 |                     0 |               19.58  |
| wind_farm_size        | wind_fixed        | {'n_turbines': 3}                       |    55.18 |       28.37 |                     7541 |                     0 |               48.07  |
| wind_farm_size        | wind_fixed        | {'n_turbines': 4}                       |    51.86 |       26.67 |                     7918 |                     0 |               80.44  |
| wind_farm_size        | wind_flex         | {'n_turbines': 1}                       |    67.38 |       34.65 |                     3062 |                     0 |                0.019 |
| wind_farm_size        | wind_flex         | {'n_turbines': 2}                       |    57.22 |       29.42 |                     4720 |                     0 |               18     |
| wind_farm_size        | wind_flex         | {'n_turbines': 3}                       |    51.99 |       26.74 |                     5651 |                     0 |               46.03  |
| wind_farm_size        | wind_flex         | {'n_turbines': 4}                       |    48.74 |       25.06 |                     6204 |                     0 |               78.09  |
| co2_price             | wind_flex         | {'co2_price': 0.0}                      |    57.22 |       29.42 |                     4720 |                     0 |               18     |
| co2_price             | wind_flex         | {'co2_price': 0.5}                      |    57.2  |       29.41 |                     4692 |                     0 |               17.99  |
| co2_price             | wind_flex         | {'co2_price': 1.0}                      |    57.22 |       29.43 |                     4731 |                     0 |               18.01  |
| co2_price             | wind_flex         | {'co2_price': 2.0}                      |    57.21 |       29.42 |                     4722 |                     0 |               17.98  |
| gas_price             | wind_flex         | {'gas_price': 2.0}                      |    57.21 |       29.42 |                     4716 |                     0 |               17.99  |
| gas_price             | wind_flex         | {'gas_price': 4.19}                     |    57.22 |       29.42 |                     4720 |                     0 |               18     |
| gas_price             | wind_flex         | {'gas_price': 8.0}                      |    57.21 |       29.42 |                     4737 |                     0 |               18     |
| battery_size          | wind_flex_battery | {'battery': [0, 0]}                     |    57.22 |       29.42 |                     4720 |                     0 |               18     |
| battery_size          | wind_flex_battery | {'battery': [2, 2]}                     |    56.88 |       29.25 |                     4603 |                     0 |               17.78  |
| battery_size          | wind_flex_battery | {'battery': [4, 4]}                     |    56.8  |       29.21 |                     4622 |                     0 |               17.62  |
| battery_size          | wind_flex_battery | {'battery': [8, 8]}                     |    56.7  |       29.16 |                     4641 |                     0 |               17.39  |
| battery_size          | wind_flex_battery | {'battery': [8, 16]}                    |    56.55 |       29.08 |                     4658 |                     0 |               17.02  |
| injection_deficit     | wind_flex         | {'max_deficit': 0}                      |    57.27 |       29.45 |                     4733 |                     0 |               18.09  |
| injection_deficit     | wind_flex         | {'max_deficit': 24}                     |    57.21 |       29.42 |                     4725 |                     0 |               17.99  |
| injection_deficit     | wind_flex         | {'max_deficit': 72}                     |    57.21 |       29.42 |                     4660 |                     0 |               18     |
| injection_deficit     | wind_flex         | {'max_deficit': 168}                    |    57.21 |       29.42 |                     4657 |                     0 |               18     |
| min_gt_online         | wind_flex_battery | {'min_gt_online': 1, 'battery': [8, 8]} |    56.7  |       29.16 |                     4641 |                     0 |               17.39  |
| min_gt_online         | wind_flex_battery | {'min_gt_online': 0, 'battery': [8, 8]} |    49.46 |       25.44 |                     1994 |                     0 |                4.104 |
| gt_fleet              | wind_flex         | {'fleet': {'main': 3}}                  |    57.22 |       29.42 |                     4720 |                     0 |               18     |
| gt_fleet              | wind_flex         | {'fleet': {'main': 2, 'small': 1}}      |    56.15 |       28.87 |                     4415 |                     0 |               16.98  |
| gt_operation_practice | wind_fixed        | {'min_gt_online': 2}                    |    80.83 |       41.56 |                    17520 |                     0 |               28.6   |
| gt_operation_practice | wind_flex         | {'min_gt_online': 2}                    |    79.98 |       41.13 |                    17520 |                     0 |               26.78  |
| line_pack             | wind_flex         | {'line_pack_hours': 0.0}                |    60.15 |       30.93 |                     6722 |                     0 |               19.45  |
| line_pack             | wind_flex         | {'line_pack_hours': 1.8}                |    57.46 |       29.55 |                     4752 |                     0 |               18.39  |
| line_pack             | wind_flex         | {'line_pack_hours': 3.6}                |    57.21 |       29.42 |                     4670 |                     0 |               17.99  |
| line_pack             | wind_flex         | {'line_pack_hours': 7.2}                |    57.01 |       29.32 |                     4709 |                     0 |               17.57  |