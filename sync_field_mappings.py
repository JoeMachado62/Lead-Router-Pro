#!/usr/bin/env python3
"""
Sync all field mappings from normalize_field_names() to field_mappings.json
Ensures field_mapper.py has access to all field transformations
"""

import json
import re

# All field mappings from normalize_field_names() in webhook_routes.py
NORMALIZE_FIELD_MAPPINGS = {
    # Name fields
    "First Name": "firstName",
    "first_name": "firstName", 
    "fname": "firstName",
    "Last Name": "lastName",
    "last_name": "lastName",
    "lname": "lastName",
    
    # Email fields
    "Your Contact Email?": "email",
    "Email": "email",
    "email_address": "email",
    "contact_email": "email",
    "Email Address": "email",
    
    # Phone fields
    "Your Contact Phone #?": "phone",
    "Phone": "phone",
    "phone_number": "phone",
    "contact_phone": "phone",
    "Phone Number": "phone",
    
    # Service-specific fields - All zip code variations
    "What Zip Code Are You Requesting Service In?": "zip_code_of_service",
    "What Zip Code Are You Requesting a Charter In?": "zip_code_of_service",
    "What Zip Code Are You Requesting a Fishing Charter In?": "zip_code_of_service",
    "What Zip Code Are You Requesting a Generator Service In?": "zip_code_of_service",
    "What Zip code are you looking for management services In?": "zip_code_of_service",
    "What Zip code are you looking to buy or sell a property In?": "zip_code_of_service",
    "What Zip code are you looking to buy or sell In?": "zip_code_of_service",
    "What Zip code are you looking to rent a dock or slip In?": "zip_code_of_service",
    "What Zip code are you looking to rent your dock or slip In?": "zip_code_of_service",
    "What Zip code are you requesting a boat club In?": "zip_code_of_service",
    "What Zip code are you requesting a charter or rental In?": "zip_code_of_service",
    "What Zip code are you requesting a lesson or equipment In?": "zip_code_of_service",
    "What Zip code are you requesting a party boat charter In?": "zip_code_of_service",
    "What Zip code are you requesting a pontoon rental or charter In?": "zip_code_of_service",
    "What Zip code are you requesting a private yacht charter In?": "zip_code_of_service",
    "What Zip code are you requesting dive services or equipment In?": "zip_code_of_service",
    "What Zip code are you requesting education or training In?": "zip_code_of_service",
    "What Zip code are you requesting financing In?": "zip_code_of_service",
    "What Zip code are you requesting insurance In?": "zip_code_of_service",
    "What Zip code are you requesting jet ski rental or tours In?": "zip_code_of_service",
    "What Zip code are you requesting kayak rental or tours In?": "zip_code_of_service",
    "What Zip code are you requesting paddleboard rental or tours In?": "zip_code_of_service",
    "What Zip code are you requesting parts In?": "zip_code_of_service",
    "What Zip code are you requesting products In?": "zip_code_of_service",
    "What Zip code are you requesting surveying In?": "zip_code_of_service",
    "Zip Code": "zip_code_of_service",
    "Service Zip Code": "zip_code_of_service",
    "Location": "zip_code_of_service",
    
    # Service request variations
    "What Specific Service(s) Do You Request?": "specific_service_needed",
    "What Specific Charter Do You Request?": "specific_service_needed",
    "What Specific service do you request?": "specific_service_needed",
    "Service Needed": "specific_service_needed",
    "Service Request": "specific_service_needed",
    "Services": "specific_service_needed",
    
    # Vessel fields
    "Your Vessel Manufacturer? ": "vessel_make",
    "Vessel Make": "vessel_make",
    "Boat Make": "vessel_make",
    "Manufacturer": "vessel_make",
    
    "Your Vessel Model": "vessel_model",
    "Vessel Model": "vessel_model",
    "Your Vessel Model or Length of Vessel in Feet?": "vessel_model",
    "Boat Model": "vessel_model",
    "Model": "vessel_model",
    
    "Your Vessel Length": "vessel_length_ft",
    "Vessel Length (ft)": "vessel_length_ft",
    "Length of Vessel in Feet": "vessel_length_ft",
    
    "Year of Vessel?": "vessel_year",
    "Vessel Year": "vessel_year",
    "Boat Year": "vessel_year",
    "Year": "vessel_year",
    
    "Is The Vessel On a Dock, At a Marina, or On a Trailer?": "vessel_location__slip",
    "Vessel Location": "vessel_location__slip",
    "Boat Location": "vessel_location__slip",
    "Location Details": "vessel_location__slip",
    
    # Timeline fields
    "When Do You Prefer Service?": "desired_timeline",
    "Timeline": "desired_timeline",
    "Service Timeline": "desired_timeline",
    "Preferred Date": "desired_timeline",
    
    # Notes fields
    "Any Special Requests or Other Information?": "special_requests__notes",
    "Special Requests": "special_requests__notes",
    "Additional Notes": "special_requests__notes",
    "Comments": "special_requests__notes",
    "Notes": "special_requests__notes",
    
    # Vendor fields
    "What is Your Company Name?": "vendor_company_name",
    "Company Name": "vendor_company_name",
    "Business Name": "vendor_company_name",
    "Services Provided": "services_provided",
    "What Main Service Does Your Company Offer?": "services_provided",
    "Service Areas": "service_zip_codes",
    "Years in Business": "years_in_business",
    
    # Contact preferences
    "How Should We Contact You (Vendor)?": "vendor_preferred_contact_method",
    "Vendor Contact Preference": "vendor_preferred_contact_method",
    "Vendor Preferred Contact Method": "vendor_preferred_contact_method",
    "vendor_preferred_contact_method": "vendor_preferred_contact_method",
    
    "How Should We Contact You Back?": "preferred_contact_method",
    "How Should We Contact You Back? ": "preferred_contact_method",
    "Contact Preference": "preferred_contact_method",
    "Preferred Contact": "preferred_contact_method",
    
    # Service categories
    "service_categories_selected": "service_categories_selected",
    "service_categorires_selected": "service_categories_selected",
    
    # Form metadata
    "Consent": "consent",
    "Preferred Partner": "vendor_preferred_partner",
    "Date": "form_submission_date",
    "Time": "form_submission_time",
    "Page URL": "source_page_url",
    "form_id": "elementor_form_id",
    "form_name": "elementor_form_name",
    
    # All lowercase variations (A-Z fields)
    "any other requests or information?": "any_other_requests_or_information",
    "any special requests or information?": "any_special_requests_or_information",
    "are you a us citizen?": "are_you_a_us_citizen",
    "are you currently involved in a dispute with the person or company you're asking about?": "are_you_currently_involved_in_a_dispute_with_the_person_or_company_you're_asking_about",
    "are you currently working with a broker or dealer?": "are_you_currently_working_with_a_broker_or_dealer",
    "are you currently working with a realtor or broker?": "are_you_currently_working_with_a_realtor_or_broker",
    "are you looking for a custom or semi custom build?": "are_you_looking_for_a_custom_or_semi_custom_build",
    "are you looking for a jet ski rental or tour?": "are_you_looking_for_a_jet_ski_rental_or_tour",
    "are you looking for a kayak rental or tour?": "are_you_looking_for_a_kayak_rental_or_tour",
    "are you looking for a paddleboard rental or tour?": "are_you_looking_for_a_paddleboard_rental_or_tour",
    "are you looking for a pontoon rental or charter?": "are_you_looking_for_a_pontoon_rental_or_charter",
    "are you looking for any specific accreditations or compliance?": "are_you_looking_for_any_specific_accreditations_or_compliance",
    "are you looking to buy or sell a vessel?": "are_you_looking_to_buy_or_sell_a_vessel",
    "are you looking to buy or sell?": "are_you_looking_to_buy_or_sell",
    "are you requesting crew or looking for a job?": "are_you_requesting_crew_or_looking_for_a_job",
    "are you the owner of the property?": "are_you_the_owner_of_the_property",
    "are you the vessel owner?": "are_you_the_vessel_owner",
    
    # B-Z fields continue...
    "brand/model of vessel looking to buy or sell?": "brand/model_of_vessel_looking_to_buy_or_sell",
    "can you briefly describe the reason for your inquiry?": "can_you_briefly_describe_the_reason_for_your_inquiry",
    "current address of vessel?": "current_address_of_vessel",
    "desired country manufacturer?": "desired_country_manufacturer",
    "desired delivery timeframe?": "desired_delivery_timeframe",
    "desired policy start date?": "desired_policy_start_date",
    "desired rental rate?": "desired_rental_rate",
    "desired survey date?": "desired_survey_date",
    "desired timeline of course or training?": "desired_timeline_of_course_or_training",
    "desired vessel length in feet?": "desired_vessel_length_in_feet",
    "destination address of vessel?": "destination_address_of_vessel",
    "did you purchase vessel yet?": "did_you_purchase_vessel_yet",
    "do you currently have boat insurance?": "do_you_currently_have_boat_insurance",
    "do you have a budget in mind?": "do_you_have_a_budget_in_mind",
    "do you have a budget in mind for this charter?": "do_you_have_a_budget_in_mind_for_this_charter",
    "do you have a desired manufacturer?": "do_you_have_a_desired_manufacturer",
    "do you have a trade-in?": "do_you_have_a_trade-in",
    "do you have capacity to take on more work?": "do_you_have_capacity_to_take_on_more_work",
    "do you own a vessel?": "do_you_own_a_vessel",
    "do you own the vessel?": "do_you_own_the_vessel",
    "do you own the vessel or what is your relationship?": "do_you_own_the_vessel_or_what_is_your_relationship",
    "do you require an emergency tow or towing membership?": "do_you_require_an_emergency_tow_or_towing_membership",
    
    # E-H fields
    "estimated length of vessel looking to buy or sell?": "estimated_length_of_vessel_looking_to_buy_or_sell",
    "finance amount requested?": "finance_amount_requested",
    "for how many people?": "for_how_many_people",
    "fuel delivery address?": "fuel_delivery_address",
    "have you been a member of a boat club before?": "have_you_been_a_member_of_a_boat_club_before",
    "how long do you request dockage??": "how_long_do_you_request_dockage",
    "how long is your space available to rent?": "how_long_is_your_space_available_to_rent",
    "how many fuel tanks?": "how_many_fuel_tanks",
    "how many gallons of fuel needed roughly?": "how_many_gallons_of_fuel_needed_roughly",
    "how many jet skis are you interested in renting?": "how_many_jet_skis_are_you_interested_in_renting",
    "how many kayaks are you interested in renting?": "how_many_kayaks_are_you_interested_in_renting",
    "how many paddleboards are you interested in renting?": "how_many_paddleboards_are_you_interested_in_renting",
    "how many people in your party?": "how_many_people_in_your_party",
    "how many people roughly on the party boat charter?": "how_many_people_roughly_on_the_party_boat_charter",
    "how many people roughly on the pontoon rental or charter?": "how_many_people_roughly_on_the_pontoon_rental_or_charter",
    "how many people roughly on the private yacht charter?": "how_many_people_roughly_on_the_private_yacht_charter",
    "how often do you plan to use a boat each month?": "how_often_do_you_plan_to_use_a_boat_each_month",
    "how soon are you looking to buy or sell?": "how_soon_are_you_looking_to_buy_or_sell",
    "how will boat be used?": "how_will_boat_be_used",
    
    # I-N fields
    "if looking for crew, how many positions?": "if_looking_for_crew,_how_many_positions",
    "is the vessel on a dock, at a marina, or on a trailer?": "is_the_vessel_on_a_dock,_at_a_marina,_or_on_a_trailer",
    "is this a one-time request or ongoing service?": "is_this_a_one-time_request_or_ongoing_service",
    "length of desired dockage in feet?": "length_of_desired_dockage_in_feet",
    "length of dock or seawall in feet?": "length_of_dock_or_seawall_in_feet",
    "longest desired rental?": "longest_desired_rental",
    "manufactuer of vessel?": "manufactuer_of_vessel",
    "number of engines?": "number_of_engines",
    "number of rooms or desired rooms?": "number_of_rooms_or_desired_rooms",
    "number of years boating experience?": "number_of_years_boating_experience",
    
    # S-T fields
    "send a link to some of your reviews?": "send_a_link_to_some_of_your_reviews",
    "shortest desired rental?": "shortest_desired_rental",
    "square feet of home or desired square feet?": "square_feet_of_home_or_desired_square_feet",
    "tell us more about your company?": "tell_us_more_about_your_company",
    "type of dockage available?": "type_of_dockage_available",
    "type of dockage requested?": "type_of_dockage_requested",
    "type of financing requested?": "type_of_financing_requested",
    
    # W fields
    "what accomodations are included?": "what_accomodations_are_included",
    "what dates specifically is the dock or slip available?": "what_dates_specifically_is_the_dock_or_slip_available",
    "what education or training do you request? ": "what_education_or_training_do_you_request",
    "what is the duration of your request?": "what_is_the_duration_of_your_request",
    "what is the vessel manufacturer?": "what_is_the_vessel_manufacturer",
    "what is the vessel model or length of vessel in feet?": "what_is_the_vessel_model_or_length_of_vessel_in_feet",
    "what is your boating experience?": "what_is_your_boating_experience",
    "what is your ideal budget?": "what_is_your_ideal_budget",
    "what management services do you request?": "what_management_services_do_you_request",
    "what product category are you interested in?": "what_product_category_are_you_interested_in",
    "what product specifically are you interested in?": "what_product_specifically_are_you_interested_in",
    "what specific attorney service do you request?": "what_specific_attorney_service_do_you_request",
    "what specific charter do you request?": "what_specific_charter_do_you_request",
    "what specific dates do you require dockage?": "what_specific_dates_do_you_require_dockage",
    "what specific parts do you request?": "what_specific_parts_do_you_request",
    "what specific sailboat charter do you request?": "what_specific_sailboat_charter_do_you_request",
    "what specific service do you request?": "what_specific_service_do_you_request",
    "what to survey?": "what_to_survey",
    "what type of boat club are you interested in??": "what_type_of_boat_club_are_you_interested_in",
    "what type of crew?": "what_type_of_crew",
    "what type of fuel do you need?": "what_type_of_fuel_do_you_need",
    "what type of party boat are you interested in?": "what_type_of_party_boat_are_you_interested_in",
    "what type of private yacht charter are you interested in?": "what_type_of_private_yacht_charter_are_you_interested_in",
    "what type of salvage do you request?": "what_type_of_salvage_do_you_request",
    "what type of trip do you request provisioning for?": "what_type_of_trip_do_you_request_provisioning_for",
    "what type of vessel are you looking to buy or sell?": "what_type_of_vessel_are_you_looking_to_buy_or_sell",
    "what type of vessel are you looking to insure?": "what_type_of_vessel_are_you_looking_to_insure",
    "what type of vessel are you looking to survey?": "what_type_of_vessel_are_you_looking_to_survey",
    "what types of boats are you most comfortable or interested in?": "what_types_of_boats_are_you_most_comfortable_or_interested_in",
    "what zip code is your vessel in most frequently?": "what_zip_code_is_your_vessel_in_most_frequently",
    "what's your current company address?": "what's_your_current_company_address",
    "when do you prefer buying or selling?": "when_do_you_prefer_buying_or_selling",
    "when do you prefer your charter?": "when_do_you_prefer_your_charter",
    "when do you prefer your charter or rental?": "when_do_you_prefer_your_charter_or_rental",
    "when do you prefer your dive charter, lessons or equipment rental?": "when_do_you_prefer_your_dive_charter,_lessons_or_equipment_rental",
    "when do you prefer your fishing charter?": "when_do_you_prefer_your_fishing_charter",
    "when do you prefer your lessons or equipment rental?": "when_do_you_prefer_your_lessons_or_equipment_rental",
    "when do you prefer your rental or charter?": "when_do_you_prefer_your_rental_or_charter",
    "when do you prefer your rental or tour?": "when_do_you_prefer_your_rental_or_tour",
    "where is the vessel located?": "where_is_the_vessel_located",
    "where is the vessel now?": "where_is_the_vessel_now",
    "who are you?": "who_are_you",
    
    # Y fields
    "your engine manufacturer or preferred engine manufacturer?": "your_engine_manufacturer_or_preferred_engine_manufacturer",
    "your generator manufacturer or preferred generator manufacturer?": "your_generator_manufacturer_or_preferred_generator_manufacturer",
    "your primary zip code?": "your_primary_zip_code"
}

def main():
    # Load current field_mappings.json
    with open('field_mappings.json', 'r') as f:
        mappings = json.load(f)
    
    added_count = 0
    updated_count = 0
    
    # Process each mapping from normalize_field_names
    for source_field, target_field in NORMALIZE_FIELD_MAPPINGS.items():
        # Also add the target field mapping to itself (for pass-through)
        fields_to_add = {
            source_field: target_field,
            target_field: target_field  # Ensure target field maps to itself
        }
        
        for field_key, field_value in fields_to_add.items():
            if field_key not in mappings['default_mappings']:
                mappings['default_mappings'][field_key] = field_value
                print(f"✅ Added: {field_key} -> {field_value}")
                added_count += 1
            elif mappings['default_mappings'][field_key] != field_value:
                old_value = mappings['default_mappings'][field_key]
                mappings['default_mappings'][field_key] = field_value
                print(f"📝 Updated: {field_key} from '{old_value}' to '{field_value}'")
                updated_count += 1
    
    # Save updated mappings
    with open('field_mappings.json', 'w') as f:
        json.dump(mappings, f, indent=2)
    
    print(f"\n✅ Sync complete!")
    print(f"   Added: {added_count} new mappings")
    print(f"   Updated: {updated_count} existing mappings")
    print(f"   Total mappings: {len(mappings['default_mappings'])}")
    
    # Verify critical fields are mapped
    critical_fields = [
        "zip_code_of_service",
        "specific_service_needed",
        "vessel_make",
        "vessel_model",
        "vessel_year",
        "vessel_location__slip",
        "special_requests__notes",
        "preferred_contact_method",
        "vendor_company_name",
        "services_provided"
    ]
    
    print("\n🔍 Verifying critical field mappings:")
    for field in critical_fields:
        if field in mappings['default_mappings']:
            print(f"   ✅ {field}")
        else:
            print(f"   ❌ {field} - MISSING!")

if __name__ == "__main__":
    main()