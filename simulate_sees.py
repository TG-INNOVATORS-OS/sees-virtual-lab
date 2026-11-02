"""
S.E.E.S. — Self-Sustaining Energy System
Digital Simulation & Mathematical Verification Script (v0.2)
Zero-Cost Computer Lab Model for ATL Feasibility Analysis
"""

import sys
from dataclasses import dataclass


@dataclass
class SEESInputs:
    aux_power_w: float           # P_aux in Watts
    duration_h: float            # t in hours
    kinetic_rec_wh: float        # E_kin in Wh
    thermal_rec_wh: float        # E_therm in Wh
    vibration_rec_wh: float      # E_vib in Wh
    system_overhead_wh: float    # E_loss in Wh
    storage_enabled: bool = False
    storage_efficiency: float = 0.88  # Round-trip efficiency (0.0 to 1.0)
    storage_capacity_wh: float = 500.0


@dataclass
class SEESOutputs:
    aux_demand_wh: float
    gross_recovered_wh: float
    net_useful_wh: float
    coverage_percent: float
    primary_required_wh: float
    storage_losses_wh: float
    kinetic_share_pct: float
    thermal_share_pct: float
    vibration_share_pct: float


def simulate_sees(inputs: SEESInputs) -> SEESOutputs:
    """Executes the mathematical energy-balance model of S.E.E.S."""
    # Auxiliary demand: E_aux = P_aux * t
    aux_demand = inputs.aux_power_w * inputs.duration_h

    # Gross recovered energy: E_gross = E_kin + E_therm + E_vib
    gross = inputs.kinetic_rec_wh + inputs.thermal_rec_wh + inputs.vibration_rec_wh

    # Deduction of power conditioning & controller overhead
    gross_post_overhead = max(0.0, gross - inputs.system_overhead_wh)

    # Optional Layer 4 Storage Buffer calculation
    storage_losses = 0.0
    delivered = gross_post_overhead

    if inputs.storage_enabled:
        routable = min(gross_post_overhead, inputs.storage_capacity_wh)
        stored_usable = routable * inputs.storage_efficiency
        storage_losses = routable * (1.0 - inputs.storage_efficiency)
        unbuffered = gross_post_overhead - routable
        delivered = stored_usable + unbuffered

    # Delivered energy cannot exceed demand or become negative
    net_useful = min(delivered, aux_demand)
    primary_required = max(0.0, aux_demand - net_useful)

    coverage_pct = (net_useful / aux_demand * 100.0) if aux_demand > 0 else 0.0

    # Pathway percentage shares
    if gross > 0:
        kin_share = (inputs.kinetic_rec_wh / gross) * 100.0
        therm_share = (inputs.thermal_rec_wh / gross) * 100.0
        vib_share = (inputs.vibration_rec_wh / gross) * 100.0
    else:
        kin_share = therm_share = vib_share = 0.0

    return SEESOutputs(
        aux_demand_wh=aux_demand,
        gross_recovered_wh=gross,
        net_useful_wh=net_useful,
        coverage_percent=coverage_pct,
        primary_required_wh=primary_required,
        storage_losses_wh=storage_losses,
        kinetic_share_pct=kin_share,
        thermal_share_pct=therm_share,
        vibration_share_pct=vib_share
    )


def run_section8_validation_checks():
    """Validates the 5 mandatory simulation criteria from Section 8 of the concept paper."""
    print("=" * 65)
    print("RUNNING SECTION 8 MANDATORY VALIDATION SUITE")
    print("=" * 65)

    # Check 1: Zero available recovery produces zero gross recovery
    out_zero = simulate_sees(SEESInputs(500, 2, 0, 0, 0, 0))
    assert out_zero.gross_recovered_wh == 0.0, "Check 1 failed: non-zero gross on zero input!"
    print("[PASS] Check 1: Zero available recovery yields exactly 0.0 Wh gross recovery.")

    # Check 2: Increasing positive auxiliary load increases demand monotonically
    out_load1 = simulate_sees(SEESInputs(100, 2, 50, 50, 10, 5))
    out_load2 = simulate_sees(SEESInputs(200, 2, 50, 50, 10, 5))
    assert out_load2.aux_demand_wh > out_load1.aux_demand_wh, "Check 2 failed: demand did not increase!"
    print("[PASS] Check 2: Increasing auxiliary load strictly increases total energy demand.")

    # Check 3: First Law of Thermodynamics - no energy created from nothing
    out_test = simulate_sees(SEESInputs(500, 2, 150, 100, 20, 30))
    assert out_test.net_useful_wh <= out_test.gross_recovered_wh, "Check 3 failed: Free energy created!"
    print("[PASS] Check 3: Conservation of Energy obeyed (Net Useful <= Gross Recovered).")

    # Check 4: Gross recovered energy is not confused with net useful energy
    assert out_test.gross_recovered_wh != out_test.net_useful_wh, "Check 4 failed: Gross equals Net despite overhead!"
    print("[PASS] Check 4: Gross (270 Wh) and Net (240 Wh) distinction strictly maintained.")

    # Check 5: Storage round-trip efficiency and capacity boundaries
    out_storage = simulate_sees(SEESInputs(500, 2, 150, 100, 20, 30, storage_enabled=True, storage_efficiency=0.88))
    assert out_storage.storage_losses_wh > 0, "Check 5 failed: storage losses not applied!"
    print("[PASS] Check 5: Storage buffer round-trip losses correctly modeled.")

    print("=" * 65)
    print("ALL 5 SECTION 8 VALIDATION CHECKS PASSED SUCCESSFULLY!\n")


def print_scenario_report(name: str, inp: SEESInputs):
    res = simulate_sees(inp)
    print(f"--- Scenario: {name} ---")
    print(f"  Auxiliary Load:        {inp.aux_power_w:.1f} W for {inp.duration_h:.1f} h -> Total Demand: {res.aux_demand_wh:.1f} Wh ({res.aux_demand_wh/1000:.2f} kWh)")
    print(f"  Gross Recovered:       {res.gross_recovered_wh:.1f} Wh (Kin: {res.kinetic_share_pct:.1f}%, Therm: {res.thermal_share_pct:.1f}%, Vib: {res.vibration_share_pct:.1f}%)")
    print(f"  Overhead / Losses:     {inp.system_overhead_wh + res.storage_losses_wh:.1f} Wh")
    print(f"  Net Useful Energy:     {res.net_useful_wh:.1f} Wh ({res.net_useful_wh/1000:.3f} kWh)")
    print(f"  Aux Demand Coverage:   {res.coverage_percent:.1f}%")
    print(f"  Primary Battery Draw:  {res.primary_required_wh:.1f} Wh (Baseline was {res.aux_demand_wh:.1f} Wh)")
    print(f"  Net Primary Energy Saved: {res.net_useful_wh:.1f} Wh\n")


if __name__ == "__main__":
    run_section8_validation_checks()

    # Section 7 Illustrative Example
    sec7_inp = SEESInputs(
        aux_power_w=500.0,
        duration_h=2.0,
        kinetic_rec_wh=150.0,
        thermal_rec_wh=100.0,
        vibration_rec_wh=20.0,
        system_overhead_wh=30.0
    )
    print_scenario_report("Section 7 Illustrative Example (Document v0.2)", sec7_inp)

    # Urban Stop-and-Go Drive Cycle
    urban_inp = SEESInputs(
        aux_power_w=400.0,
        duration_h=3.0,
        kinetic_rec_wh=450.0,
        thermal_rec_wh=90.0,
        vibration_rec_wh=25.0,
        system_overhead_wh=40.0,
        storage_enabled=True
    )
    print_scenario_report("Urban Stop-and-Go (High Kinetic Regeneration)", urban_inp)

    # Highway Long Haul
    highway_inp = SEESInputs(
        aux_power_w=600.0,
        duration_h=4.0,
        kinetic_rec_wh=180.0,
        thermal_rec_wh=380.0,
        vibration_rec_wh=15.0,
        system_overhead_wh=35.0
    )
    print_scenario_report("Highway Long-Haul (Continuous Thermal Gradient)", highway_inp)
