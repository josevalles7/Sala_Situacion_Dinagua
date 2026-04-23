"""HydroSOS scripts package.

Public API for flow aggregation and hydrological status computation.
"""

from .flow_aggregation import (
	import_data as import_flow_data,
	calculate_monthly as calculate_monthly_flow,
	import_monthly as import_monthly_flow,
	calculate_accumulated,
)

from .hydrological_status import (
	monthly_status,
	bimonthly_status,
	quarterly_status,
	semiannual_status,
	annualy_status,
	export_csv,
	csv_to_json,
)

__all__ = [
	"import_flow_data",
	"calculate_monthly_flow",
	"import_monthly_flow",
	"calculate_accumulated",
	"monthly_status",
	"bimonthly_status",
	"quarterly_status",
	"semiannual_status",
	"annualy_status",
	"export_csv",
	"csv_to_json",
]

__version__ = "0.1.0"
