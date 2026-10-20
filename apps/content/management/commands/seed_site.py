from django.core.management.base import BaseCommand

from apps.booking.models import PricingGuideRow
from apps.booking.quote_prices import seed_quote_prices
from apps.company.models import CompanyProfile
from apps.content.models import Article, FAQ, LocationPage, ServicePage, SolutionPage
from apps.redirects.models import LegacyRedirect


ABOUT = (
    "TheCleanHandy is a New York City cleaning and moving services company specializing in "
    "move-in and move-out cleaning, moving support, and commercial cleaning. The company serves "
    "residential customers, landlords, property managers, and businesses throughout NYC."
)


def service(**kwargs):
    return kwargs


SERVICES = [
    service(
        slug="moving-services-nyc",
        name="Moving Services NYC",
        category="moving",
        menu="moving",
        menu_order=1,
        primary_keyword="moving services NYC",
        secondary_keywords="apartment movers NYC, small moving service NYC",
        seo_title="Moving Services NYC | TheCleanHandy",
        meta_description="Company-performed moving help for NYC apartments and small relocations. Request a written quote from TheCleanHandy.",
        short_description="TheCleanHandy crews move apartments and small households inside New York City. The quote states the crew size and whether a truck, packing, or insurance is included.",
        who_it_is_for="Renters, owners, and managers moving within NYC who want the same company that can also clean the apartment.",
        included="Walk-through of the access plan you send with the quote\nLoading and unloading by a TheCleanHandy crew\nPlacement of furniture in the rooms you name\nBasic protection for floors and doorways on the path of the move",
        checklist="Building address and floor\nElevator or walk-up\nCertificate of insurance if the building requires one\nDate and the time window the building allows\nItems that need two people",
        add_ons="Packing, when it is turned on for the company\nA truck or van, when it is turned on for the company\nMove-out or move-in cleaning on the same booking",
        timeline="Send the quote request with borough, size, and access. Staff reply with a written scope. The crew arrives in the window you accept.",
        pricing_factors="Stairs, long carries, elevator reservations, and the amount of furniture change the crew and the hours. The site does not publish a flat moving rate.",
        bookable=True,
    ),
    service(
        slug="apartment-moving-nyc",
        name="Apartment Moving",
        category="moving",
        menu="moving",
        menu_order=2,
        primary_keyword="apartment moving NYC",
        seo_title="Apartment Moving NYC | TheCleanHandy",
        meta_description="Apartment moves in New York City performed by TheCleanHandy crews, with building access included in the quote.",
        short_description="Apartment moves cover walk-ups and elevator buildings. The quote is built around the floor, the elevator rules, and what has to leave the unit.",
        who_it_is_for="Tenants and owners moving a one-bedroom, two-bedroom, or similar apartment in New York City.",
        included="Crew for loading and unloading the apartment\nFurniture carried along the path the building allows\nCoordination notes for the super or doorman when you provide them",
        checklist="Floor number\nWalk-up or elevator\nCOI requirement\nDisassembly only if you ask for it in the notes",
        add_ons="Move-out cleaning after the furniture leaves\nMove-in cleaning before the furniture arrives",
        timeline="Most apartment quotes are answered after the building rules are known. Book early enough for the elevator reservation.",
        pricing_factors="Floor, stairs, and how full the apartment is. A studio and a three-bedroom are not the same quote.",
        bookable=True,
    ),
    service(
        slug="small-moves-nyc",
        name="Small Moves",
        category="moving",
        menu="moving",
        menu_order=3,
        primary_keyword="small moving service NYC",
        seo_title="Small Moves NYC | TheCleanHandy",
        meta_description="Small NYC moves for a few rooms of furniture, performed by TheCleanHandy rather than a lead marketplace.",
        short_description="Small moves are for a limited set of furniture and boxes, not a whole house. Say what is moving so the crew size matches the job.",
        who_it_is_for="People moving a few pieces between apartments, or shifting furniture for a landlord between tenants.",
        included="A crew sized to the list you send\nCarry from the current room to the destination room or vehicle",
        checklist="A list of the large items\nBoth addresses if there are two\nStairs at each end",
        add_ons="Cleaning the unit you are leaving\nAssembly of furniture that was taken apart",
        timeline="Smaller lists can often be scheduled with less lead time than a full apartment, subject to building rules.",
        pricing_factors="Item count, stairs, and distance between doors. There is no citywide small-move price on this site.",
        bookable=True,
    ),
    service(
        slug="moving-labor-nyc",
        name="Moving Labor",
        category="moving",
        menu="moving",
        menu_order=4,
        primary_keyword="moving labor NYC",
        seo_title="Moving Labor NYC | TheCleanHandy",
        meta_description="Moving labor in NYC from TheCleanHandy crews. Truck coverage is stated only when the company has it turned on.",
        short_description="Moving labor is the crew: loading, unloading, and carrying. A truck is mentioned on the page only when the company profile says one is available.",
        who_it_is_for="Customers who need people for the heavy work and will confirm transportation in the written quote.",
        included="Labor for the hours and headcount on the quote\nCareful carries through the building path",
        checklist="How many people you think you need\nWhether you already have a truck\nThe heaviest items",
        add_ons="Company truck, only if that capability is on\nPacking, only if that capability is on",
        timeline="Labor is scheduled for a start time. Overtime beyond the quoted scope is discussed before the crew continues.",
        pricing_factors="Hours, headcount, stairs, and whether the quote also includes a vehicle.",
        bookable=True,
    ),
    service(
        slug="moving-and-cleaning-nyc",
        name="Moving and Cleaning",
        category="moving",
        menu="moving",
        menu_order=5,
        primary_keyword="moving and cleaning NYC",
        seo_title="Moving and Cleaning NYC | TheCleanHandy",
        meta_description="Book TheCleanHandy moving labor and move-in or move-out cleaning on one NYC quote.",
        short_description="One request can cover the move and the cleaning. The written quote splits the crew work from the cleaning checklist so each part is clear.",
        who_it_is_for="Anyone leaving or entering an NYC apartment who wants both jobs from the same company.",
        included="Moving labor as described on the moving pages\nMove-out or move-in cleaning as described on those service pages\nOne point of contact for the schedule",
        checklist="Which day the furniture moves\nWhich day the cleaning should happen\nWhether cleaning is before furniture arrives or after it leaves",
        add_ons="Inside appliances\nInterior windows\nExtra rooms beyond the size band",
        timeline="Cleaning is usually booked for after the furniture is out, or before it arrives. The quote names both windows.",
        pricing_factors="You are quoting two services. Each has its own scope, and the total is the sum of the written estimate.",
        bookable=True,
    ),
    service(
        slug="move-in-out-cleaning-nyc",
        name="Move-In / Move-Out Cleaning NYC",
        category="move_cleaning",
        menu="",
        menu_order=0,
        primary_keyword="move in out cleaning NYC",
        seo_title="Move-In / Move-Out Cleaning NYC | TheCleanHandy",
        meta_description="Move-in and move-out cleaning for NYC apartments. See what is included and request a quote from TheCleanHandy.",
        short_description="This is the combined service for people who need a home cleaned because someone is moving in or out. Separate pages cover move-in and move-out on their own.",
        who_it_is_for="Tenants, landlords, buyers, and sellers who need the apartment cleaned around a move.",
        included="Kitchens and bathrooms detailed for an empty or nearly empty home\nInterior cabinets and drawers\nAppliance exteriors, and interiors when the quote includes them\nFloors vacuumed or mopped\nInterior windows",
        checklist="Kitchen surfaces, sink, and appliance fronts\nBathroom fixtures, tile, and floors\nBedrooms and living areas dusted\nBaseboards, doors, and switches\nCobwebs and built-up dirt",
        add_ons="Inside fridge and oven\nWalls where they can be wiped without painting\nA moving crew on the same request",
        timeline="For a 1,000–1,500 sq ft move-in/out, the published time guide is 2 cleaners for about 5 hours. Larger bands take more people or more hours. The quote confirms the visit.",
        pricing_factors="Size band, how dirty the kitchen and baths are, and whether the home is empty. Heavy clutter or construction material is outside the standard time guide.",
        bookable=True,
    ),
    service(
        slug="move-out-cleaning-nyc",
        name="Move-Out Cleaning NYC",
        category="move_cleaning",
        menu="cleaning",
        menu_order=2,
        primary_keyword="move out cleaning NYC",
        seo_title="Move-Out Cleaning NYC | TheCleanHandy",
        meta_description="Move-out cleaning in NYC for tenants and landlords, including kitchens, baths, floors, and a written quote.",
        short_description="Move-out cleaning is for the apartment you are handing back. The goal is a documented clean of the empty or nearly empty home before the inspection.",
        who_it_is_for="Tenants who want the unit ready for a landlord walkthrough, and landlords taking a unit back.",
        included="Empty kitchen and bath detail\nInside cabinets and drawers\nFloors\nInterior glass\nDust on baseboards, doors, and sills",
        checklist="Kitchen: counters, sink, cabinet fronts, appliance exteriors\nBathrooms: toilet, tub or shower, sink, floor\nBedrooms: closets, floors, windowsills\nWalls: spot wiping where the surface allows\nWindows: interior glass",
        add_ons="Inside oven, fridge, and microwave\nBalcony sweep if access is safe\nExtra cleaning after a paint job, quoted as post-renovation instead",
        timeline="Book after the furniture is out when you can. The published guide for 1,000–1,500 sq ft move-in/out work is 2 cleaners and about 5 hours.",
        pricing_factors="Square footage, condition, and whether appliances are emptied. A security deposit decision belongs to the landlord; the clean is the scope on the quote.",
        bookable=True,
    ),
    service(
        slug="move-in-cleaning-nyc",
        name="Move-In Cleaning NYC",
        category="move_cleaning",
        menu="cleaning",
        menu_order=1,
        primary_keyword="move in cleaning NYC",
        secondary_keywords="apartment move in cleaning, new apartment cleaning NYC",
        seo_title="Move-In Cleaning NYC | TheCleanHandy",
        meta_description="Move-in cleaning before furniture arrives in a New York apartment. TheCleanHandy cleans the empty home first.",
        short_description="Move-in cleaning happens before your furniture is in the apartment. The crew cleans the empty rooms so you unpack onto clean surfaces.",
        who_it_is_for="New tenants and owners who want the kitchen, baths, and floors cleaned before move-in day.",
        included="Empty-unit dust and dirt removal\nKitchen and bathrooms\nInside cabinets when they are empty\nFloors washed\nInterior windows",
        checklist="Cabinets and drawers wiped before boxes arrive\nAppliance exteriors\nBathroom fixtures sanitized\nFloors in every room on the quote\nLight switches and door handles",
        add_ons="Inside appliances if the previous tenant left them empty\nCloset shelves\nMoving help on a later day",
        timeline="Schedule the clean for a day you have keys and before the truck arrives. Furniture in the rooms slows the work and changes the quote.",
        pricing_factors="Size, how long the apartment sat empty, and whether paint or construction dust is present. Construction dust is quoted as post-renovation cleaning.",
        bookable=True,
    ),
    service(
        slug="apartment-move-out-cleaning-nyc",
        name="Apartment Move-Out Cleaning",
        category="move_cleaning",
        menu="",
        menu_order=0,
        primary_keyword="apartment move out cleaning NYC",
        seo_title="Apartment Move-Out Cleaning NYC | TheCleanHandy",
        meta_description="Apartment move-out cleaning in NYC, planned around walk-ups, elevators, and landlord handoff.",
        short_description="This page is the apartment version of move-out cleaning: smaller rooms, building access, and a handoff to a landlord or manager.",
        who_it_is_for="People leaving a New York apartment, including walk-ups where the crew must carry supplies up stairs.",
        included="The move-out checklist, scaled to an apartment rather than a house\nAttention to kitchens and the bathroom that the next inspection usually covers",
        checklist="Fridge and oven exteriors, interiors if emptied\nCabinet shelves\nTub, tile, and toilet\nFloors after furniture is gone\nWindow tracks that can be reached from inside",
        add_ons="A second visit if the landlord's list adds rooms\nTurnover cleaning booked by the manager instead of the tenant",
        timeline="Ask for a slot after your mover leaves and before the keys are due. Tell us the floor so the crew plans the carry.",
        pricing_factors="Apartment size band, floor access, and how much is left in the kitchen. The time guide starts at 2 cleaners and about 5 hours for 1,000–1,500 sq ft.",
        bookable=True,
    ),
    service(
        slug="rental-turnover-cleaning-nyc",
        name="Rental Turnover Cleaning",
        category="move_cleaning",
        menu="cleaning",
        menu_order=5,
        primary_keyword="apartment turnover cleaning NYC",
        seo_title="Rental Turnover Cleaning NYC | TheCleanHandy",
        meta_description="Turnover cleaning between NYC tenants for landlords and property managers, with a written quote per unit.",
        short_description="Turnover cleaning is the reset between tenants: move-out detail, then a unit that is ready for the next move-in.",
        who_it_is_for="Landlords and property managers with one or more NYC rentals.",
        included="Full empty-unit clean\nKitchen and bath reset\nFloors\nNotes if a room could not be cleaned because of damage or missing utilities",
        checklist="Appliances\nCabinets\nBathrooms\nFloors and baseboards\nInterior glass\nClosets",
        add_ons="Recurring cleans between guest stays\nMove-in clean on a second date\nSeveral units on one account",
        timeline="A turnover is scheduled around the keys. Multiple units are sequenced so one crew is not double-booked.",
        pricing_factors="Each unit is quoted from its size and condition. A portfolio does not force one blended price.",
        bookable=True,
    ),
    service(
        slug="deep-cleaning-nyc",
        name="Deep Cleaning",
        category="move_cleaning",
        menu="cleaning",
        menu_order=3,
        primary_keyword="deep cleaning NYC",
        seo_title="Deep Cleaning NYC | TheCleanHandy",
        meta_description="Deep cleaning for NYC homes, including the published time guide and a written quote from TheCleanHandy.",
        short_description="Deep cleaning is a fuller reset than a routine visit. It is often booked before or after a move when the home needs more than a surface clean.",
        who_it_is_for="Households that need kitchens, baths, and built-up dirt addressed, whether or not they are moving the same week.",
        included="Detailed kitchen and baths\nBaseboards and doors\nFloors\nInterior glass\nDust on reachable surfaces",
        checklist="Kitchen degrease on exterior surfaces\nBathroom fixtures and floors\nBedroom and living area dusting\nBehind doors and along trim",
        add_ons="Inside appliances\nInside cabinets if they are emptied",
        timeline="The published guide for deep cleaning at 1,000–1,500 sq ft is 2 cleaners for about 5 hours. The quote can differ if the home is occupied and full.",
        pricing_factors="Occupancy, clutter, and kitchen condition. The time guide assumes the crew can reach the surfaces.",
        bookable=True,
    ),
    service(
        slug="post-renovation-cleaning-nyc",
        name="Post-Renovation Cleaning",
        category="move_cleaning",
        menu="cleaning",
        menu_order=4,
        primary_keyword="post renovation cleaning NYC",
        seo_title="Post-Renovation Cleaning NYC | TheCleanHandy",
        meta_description="Post-renovation cleaning in NYC after paint or construction dust. The time guide and quote assume the site is ready to clean.",
        short_description="Post-renovation cleaning removes the dust and debris left after paint, plaster, or light construction, once the trades are finished.",
        who_it_is_for="Owners and managers who need a unit cleaned after work and before a tenant or buyer walks in.",
        included="Dust removal from reachable surfaces\nFloors\nBath and kitchen reset after the work\nDebris that can be bagged without hauling construction waste",
        checklist="Sills, trim, and fixtures\nFloors after dust has settled\nBathrooms used by the work crew\nKitchen if it was in the work zone",
        add_ons="A second pass after punch-list work\nMove-in cleaning once the dust is gone",
        timeline="The published guide for post-renovation at 1,000–1,500 sq ft is 3 cleaners for about 6 hours. Larger homes use the next bands on the pricing page.",
        pricing_factors="Dust volume and whether heavy material or equipment is still in the rooms. If the site is not ready, the quoted time does not apply.",
        bookable=True,
    ),
    service(
        slug="post-event-cleaning-nyc",
        name="Post-Event Cleaning",
        category="additional",
        menu="",
        menu_order=0,
        primary_keyword="post event cleaning NYC",
        seo_title="Post-Event Cleaning NYC | TheCleanHandy",
        meta_description="Cleaning after an event in an NYC home or small venue. TheCleanHandy quotes the space after you describe it.",
        short_description="Post-event cleaning puts a home or small space back in order after guests: surfaces, floors, baths, and trash you have bagged or asked the crew to remove.",
        who_it_is_for="Hosts and managers who need a reset after a gathering, not a daily janitorial contract.",
        included="Surface wipe-down\nFloors\nBathrooms\nKitchen counters and sink",
        checklist="Guest bathrooms\nKitchen\nFloors in the rooms that were used\nTrash if it is already collected or listed on the quote",
        add_ons="Next-day turnover if the space is a rental\nInterior glass",
        timeline="The visit is scheduled for after the event ends and the guests are gone.",
        pricing_factors="Guest count is less useful than rooms used and the condition of the kitchen. The quote uses that description.",
        bookable=True,
    ),
    service(
        slug="commercial-cleaning-nyc",
        name="Commercial Cleaning NYC",
        category="commercial",
        menu="commercial",
        menu_order=2,
        primary_keyword="commercial cleaning NYC",
        secondary_keywords="commercial cleaners NYC",
        seo_title="Commercial Cleaning NYC | TheCleanHandy",
        meta_description="Commercial cleaning for NYC offices, retail, and managed properties. Frequency and price are on the written quote.",
        short_description="Commercial cleaning is recurring or scheduled work in a business space: floors, restrooms, trash, and the surfaces employees and customers touch.",
        who_it_is_for="Businesses, retailers, and managers who need a cleaner on a schedule rather than a one-time apartment clean.",
        included="Restrooms\nFloors\nTrash removal to the building's disposal point\nHigh-touch surfaces\nBreak area counters",
        checklist="Desks or sales floor as agreed\nRestroom fixtures and restock if you supply products\nKitchenette\nEntry glass that can be reached from inside",
        add_ons="Night or early visits\nA one-time reset before a new tenant\nRetail floor detail",
        timeline="The first visit confirms access, alarms, and keys. After that, the quote names the days.",
        pricing_factors="Square footage, restroom count, days per week, and after-hours rules. There is no single commercial rate on this site.",
        bookable=True,
    ),
    service(
        slug="office-cleaning-nyc",
        name="Office Cleaning",
        category="commercial",
        menu="commercial",
        menu_order=1,
        primary_keyword="office cleaning NYC",
        seo_title="Office Cleaning NYC | TheCleanHandy",
        meta_description="Office cleaning in New York City with a schedule, a checklist, and a written quote from TheCleanHandy.",
        short_description="Office cleaning keeps a workplace presentable: desks, restrooms, kitchenettes, trash, and floors, on the days the quote lists.",
        who_it_is_for="Offices that want a recurring clean or a reset before staff or a new tenant arrives.",
        included="Dust and wipe of desks and tables\nHigh-touch points such as handles and switches\nTrash and liner replacement\nVacuum or mop\nRestrooms\nKitchenette counters and the outside of appliances",
        checklist="Workstations\nConference rooms\nRestrooms\nKitchenette\nFloors\nInterior glass at the entry if it is in the scope",
        add_ons="Interior window detail\nCarpet attention beyond vacuuming\nAfter-hours timing",
        timeline="Daily, weekly, or a custom rhythm. A one-time office clean uses the same checklist with a single date.",
        pricing_factors="Size, number of restrooms, and how many days a week. The residential time guide is a reference for homes, not a substitute for an office quote.",
        bookable=True,
    ),
    service(
        slug="retail-cleaning-nyc",
        name="Retail Cleaning",
        category="commercial",
        menu="commercial",
        menu_order=3,
        primary_keyword="retail cleaning NYC",
        seo_title="Retail Cleaning NYC | TheCleanHandy",
        meta_description="Retail cleaning in NYC for sales floors, fitting rooms, and restrooms. TheCleanHandy quotes the store you describe.",
        short_description="Retail cleaning covers the sales floor, fitting rooms, entry, and restrooms on a schedule that fits opening hours.",
        who_it_is_for="Shops and showrooms that need the customer areas cleaned without interrupting the day more than the quote allows.",
        included="Floors\nFitting rooms\nEntry glass reachable from inside\nRestrooms\nDust on fixtures you clear",
        checklist="Sales floor\nCash wrap\nFitting rooms\nRestroom\nStockroom only if it is on the quote",
        add_ons="Opening or closing visits\nA deeper clean before a reset of the floor",
        timeline="Visits are placed before opening or after close when you need the floor empty.",
        pricing_factors="Store size, fitting-room count, and whether the visit is before customers arrive.",
        bookable=True,
    ),
    service(
        slug="property-management-cleaning",
        name="Property Management Cleaning",
        category="commercial",
        menu="commercial",
        menu_order=4,
        primary_keyword="property management cleaning NYC",
        seo_title="Property Management Cleaning NYC | TheCleanHandy",
        meta_description="Cleaning for NYC property managers: turnovers, move-in preparation, and common-area or unit visits on one account.",
        short_description="Property management cleaning is unit turnover plus the recurring work a manager actually schedules across more than one address.",
        who_it_is_for="Managers responsible for several apartments or a small building in New York City.",
        included="Turnover cleans between tenants\nMove-in preparation\nRecurring unit or common-area cleans named on the quote",
        checklist="Empty-unit kitchen and bath\nFloors\nNotes on damage the crew can see but will not repair\nAccess instructions per building",
        add_ons="Emergency visit when a unit has to be shown\nInvoices per job\nA property-manager login with multiple addresses",
        timeline="Each unit gets its own date. The account keeps the addresses so the next request does not start from zero.",
        pricing_factors="Unit size and condition, plus how many addresses are active. Invoices are issued per job by staff.",
        bookable=True,
    ),
    service(
        slug="recurring-commercial-cleaning",
        name="Recurring Commercial Cleaning",
        category="commercial",
        menu="commercial",
        menu_order=5,
        primary_keyword="recurring commercial cleaning NYC",
        seo_title="Recurring Commercial Cleaning NYC | TheCleanHandy",
        meta_description="Recurring commercial cleaning in NYC. The quote names the days, the rooms, and the price for that schedule.",
        short_description="Recurring cleaning is the same checklist on a repeating schedule, for an office, shop, or managed space.",
        who_it_is_for="Operators who want a standing visit instead of booking a one-time clean each time.",
        included="The commercial checklist on each visit\nA named rhythm: daily, weekly, or another pattern on the quote",
        checklist="Restrooms every visit\nFloors every visit\nTrash every visit\nDetail tasks on the days the quote assigns them",
        add_ons="A periodic deeper clean\nExtra visit after an event",
        timeline="The first month confirms that the schedule matches the building's access rules. Changes are written, not assumed.",
        pricing_factors="Visits per week and the size of the space. A five-day office is not priced like a weekly shop.",
        bookable=True,
    ),
    service(
        slug="additional-services",
        name="Additional Services",
        category="additional",
        menu="",
        menu_order=0,
        primary_keyword="handyman services NYC",
        seo_title="Additional Services | TheCleanHandy",
        meta_description="Assembly, mounting, and painting remain available from TheCleanHandy alongside moving and cleaning.",
        short_description="Moving and cleaning are the main services. Assembly, mounting, and painting are still offered when a job needs them.",
        who_it_is_for="Customers who already know TheCleanHandy for those tasks, or who need one of them alongside a move.",
        included="A quote for the specific task\nWork performed by TheCleanHandy, not listed as a lead for someone else",
        checklist="What needs to be assembled, hung, or painted\nPhotos or measurements in the notes if you have them",
        add_ons="Combine with moving or cleaning on one request by describing both in the notes",
        timeline="These tasks are scheduled around the primary moving and cleaning calendar.",
        pricing_factors="The task, the wall or furniture type, and access. There is no flat handyman rate on this site.",
        bookable=False,
    ),
    service(
        slug="assembly",
        name="Assembly",
        category="additional",
        menu="",
        menu_order=0,
        primary_keyword="furniture assembly NYC",
        seo_title="Furniture Assembly NYC | TheCleanHandy",
        meta_description="Furniture assembly in NYC from TheCleanHandy. Describe the pieces and request a quote.",
        short_description="Assembly covers furniture that arrives flat-packed. List the pieces so the quote matches the time.",
        who_it_is_for="People setting up an apartment after a move.",
        included="Assembly of the items listed on the quote\nPackaging removed to the building's disposal point if that is in the notes",
        checklist="Item list\nWhether instructions are on site\nRoom where each piece goes",
        add_ons="Mounting a piece that also needs a wall anchor\nMoving the boxed furniture inside first",
        timeline="Assembly is easier after the boxes are in the room. Say if the crew should also carry them up.",
        pricing_factors="Number of pieces and how complex the hardware is.",
        bookable=True,
    ),
    service(
        slug="mounting",
        name="Mounting",
        category="additional",
        menu="",
        menu_order=0,
        primary_keyword="TV mounting NYC",
        seo_title="Mounting NYC | TheCleanHandy",
        meta_description="Mounting for TVs, shelves, and similar items in NYC apartments. The quote depends on the wall.",
        short_description="Mounting fastens the item you name to the wall, after you confirm the building allows it.",
        who_it_is_for="Tenants and owners who need a television, shelf, or similar item hung.",
        included="Mounting the listed items\nHardware appropriate to the wall when it can be confirmed on site",
        checklist="What is being mounted\nWall type if you know it\nBuilding permission if the lease requires it",
        add_ons="Several items on one visit\nAssembly of the furniture first",
        timeline="A short visit once the item and the bracket are in the apartment.",
        pricing_factors="Number of items and the wall. Plaster, brick, and drywall are not the same job.",
        bookable=True,
    ),
    service(
        slug="painting",
        name="Painting",
        category="additional",
        menu="",
        menu_order=0,
        primary_keyword="painting NYC",
        seo_title="Painting NYC | TheCleanHandy",
        meta_description="Painting for NYC rooms that need it alongside a turnover or a move. TheCleanHandy quotes the rooms you list.",
        short_description="Painting covers the rooms listed on the quote. It is a supporting service, not the company's main offer.",
        who_it_is_for="Landlords refreshing a unit, or residents painting before or after a move.",
        included="Paint on the walls named in the quote\nBasic protection of floors and fixtures in those rooms",
        checklist="Which rooms\nWhether paint is supplied\nWhether the room is empty",
        add_ons="Post-renovation cleaning after the paint dries\nCeiling only if it is written into the quote",
        timeline="Paint needs dry time before furniture or a deep clean. The quote should leave that gap.",
        pricing_factors="Room count, ceiling height, and whether the room is empty. Color changes and repairs are extra when they are not in the scope.",
        bookable=False,
    ),
]


LOCATIONS = [
    {
        "slug": "manhattan",
        "name": "Manhattan",
        "seo_title": "Moving & Cleaning in Manhattan | TheCleanHandy",
        "meta_description": "Manhattan moving, move-out cleaning, and office cleaning, with elevator and walk-up access called out in the quote.",
        "introduction": "Manhattan jobs are usually about the building, not the distance. Elevator reservations, certificates of insurance, and walk-ups change the crew plan.",
        "neighborhoods": "Upper East Side\nUpper West Side\nMidtown\nChelsea\nHarlem\nFinancial District\nEast Village\nWashington Heights",
        "body": "A Manhattan apartment move needs the floor, the elevator window, and whether the board wants a certificate of insurance. Move-out cleaning is booked after the furniture is out when the lease date allows it. Offices in Midtown and downtown are quoted as commercial cleaning, with after-hours access written down. TheCleanHandy does not publish a separate page for every Manhattan neighborhood.",
    },
    {
        "slug": "brooklyn",
        "name": "Brooklyn",
        "seo_title": "Moving & Cleaning in Brooklyn | TheCleanHandy",
        "meta_description": "Brooklyn apartment moves, brownstone walk-ups, and move-out cleaning from TheCleanHandy.",
        "introduction": "Brooklyn work mixes elevator buildings and walk-up brownstones. The stairs are part of the quote for both moving and cleaning.",
        "neighborhoods": "Williamsburg\nBrooklyn Heights\nPark Slope\nBushwick\nBay Ridge\nBedford-Stuyvesant\nDumbo\nCrown Heights",
        "body": "Brownstones often mean a parlor floor and a garden level, with tight turns. Say which floor the furniture starts on. Move-out cleans in rentals are scheduled around the key return, and turnover cleans for managers can cover more than one unit if each address is on the account. Commercial cleaning in Brooklyn storefronts is quoted from the sales floor and the restroom, not from a Manhattan office template.",
    },
    {
        "slug": "queens",
        "name": "Queens",
        "seo_title": "Moving & Cleaning in Queens | TheCleanHandy",
        "meta_description": "Queens moving and cleaning for apartments and houses, including Astoria and other neighborhoods TheCleanHandy serves.",
        "introduction": "Queens includes both apartment buildings and houses. The quote asks which one, because a house and a walk-up apartment do not take the same crew.",
        "neighborhoods": "Astoria\nLong Island City\nJackson Heights\nForest Hills\nFlushing\nSunnyside\nRidgewood\nJamaica",
        "body": "Astoria has its own page because the company's published location is Astoria, NY 11106. Long Island City is served as part of Queens and is not a separate doorway page. House moves should mention stairs, a garage, or a driveway. Apartment move-outs follow the same checklist as the rest of the city: kitchen, baths, floors, and interior glass, with the time guide used as a starting point.",
    },
    {
        "slug": "bronx",
        "name": "Bronx",
        "seo_title": "Moving & Cleaning in the Bronx | TheCleanHandy",
        "meta_description": "Bronx moving, move-out cleaning, and commercial cleaning from TheCleanHandy crews.",
        "introduction": "Bronx visits cover apartments and houses. Tell the crew the floor and whether the building has an elevator before the day of the job.",
        "neighborhoods": "Riverdale\nKingsbridge\nFordham\nMott Haven\nPelham Bay\nThrogs Neck\nConcourse",
        "body": "A Bronx move-out is still an empty-unit clean: cabinets, baths, floors, and appliances as the quote lists them. Houses need a note about extra floors. Commercial spaces are quoted separately from apartments. TheCleanHandy schedules Bronx work with the same written estimate used in the other boroughs.",
    },
    {
        "slug": "astoria",
        "name": "Astoria",
        "seo_title": "Moving & Cleaning in Astoria | TheCleanHandy",
        "meta_description": "Astoria moving and move-in/out cleaning from TheCleanHandy, the company's published New York location.",
        "introduction": "Astoria is called out on its own because TheCleanHandy's published location is Astoria, NY 11106, and the neighborhood is a regular service area.",
        "neighborhoods": "Astoria\nDitmars\nSteinway\nAstoria Heights",
        "body": "Many Astoria buildings are walk-ups. A move or a cleaning should include the floor so the crew is not planned as if there were an elevator. Move-out cleaning follows the apartment checklist, and commercial work along the avenues is quoted as a shop or office rather than as a home. The street address stays blank on the site until a full street address is entered in the company profile.",
    },
    {
        "slug": "staten-island",
        "name": "Staten Island",
        "seo_title": "Moving & Cleaning on Staten Island | TheCleanHandy",
        "meta_description": "Staten Island moving, move-out cleaning, and commercial cleaning from TheCleanHandy crews.",
        "introduction": "Staten Island jobs cover houses and apartment buildings. The quote includes the floor, parking, and the bridge or ferry trip the crew will take.",
        "neighborhoods": "St. George\nStapleton\nTodt Hill\nNew Dorp\nGreat Kills\nTottenville\nPort Richmond",
        "body": "A Staten Island move should say whether the stop is a house or an apartment, and which floor the furniture starts on. Houses often have a driveway. Apartment buildings may need an elevator window. Move-out cleaning uses the same empty-unit checklist as the other boroughs. Commercial spaces are quoted from the rooms on the request, not from a Manhattan office template.",
    },
    {
        "slug": "long-island",
        "name": "Long Island",
        "seo_title": "Moving & Cleaning on Long Island | TheCleanHandy",
        "meta_description": "Long Island moving and cleaning for houses and apartments in Nassau and Suffolk, quoted by TheCleanHandy.",
        "introduction": "Long Island work is mostly houses, with apartments in the busier towns. Driveway access and travel time are part of the quote.",
        "neighborhoods": "Great Neck\nGarden City\nHempstead\nLong Beach\nHicksville\nHuntington\nBabylon\nSmithtown",
        "body": "Tell the crew whether the job is a house or an apartment, and whether there is a driveway, a garage, or stairs. Nassau stops are closer to the city. Suffolk stops need the town on the quote so the travel is priced before the day of the job. Move-out and move-in cleaning follow the same checklist used in the city. Offices and shops are quoted as commercial cleaning.",
    },
    {
        "slug": "new-jersey",
        "name": "New Jersey",
        "seo_title": "Moving & Cleaning in New Jersey | TheCleanHandy",
        "meta_description": "Moving and cleaning in New Jersey, including Hudson County and nearby towns, with travel confirmed on the quote.",
        "introduction": "New Jersey visits start with Hudson County and nearby towns. Farther stops are confirmed on the quote once the town and the travel are clear.",
        "neighborhoods": "Jersey City\nHoboken\nNewark\nFort Lee\nHackensack\nMontclair\nElizabeth\nEdison",
        "body": "A New Jersey apartment move needs the floor and the elevator or walk-up, the same as a city building. Houses need a note about stairs, a driveway, or a garage. Hudson County is the usual first stop from the city. Towns farther out should be named on the request so the crew and the travel are written into the estimate. Cleaning checklists do not change because the address is across the river.",
    },
]


SOLUTIONS = [
    {
        "slug": "property-managers",
        "name": "For Property Managers",
        "seo_title": "Cleaning for NYC Property Managers | TheCleanHandy",
        "meta_description": "Turnover, move-out, and recurring cleaning for NYC property managers, with multiple properties on one account.",
        "introduction": "Cleaning and turnover services for NYC property managers who need units reset between tenants and a record of each quote.",
        "body": "A manager can keep more than one property on an account and request move-out cleaning, move-in preparation, or a recurring visit per address. Emergency timing is a scheduling question on the quote, not a guaranteed arrival window. Invoices are created by staff against an accepted job. The account is the dedicated contact record: the same company phone and email, tied to your properties. TheCleanHandy does not publish a blended portfolio rate.",
    },
    {
        "slug": "businesses",
        "name": "For Businesses",
        "seo_title": "Commercial Cleaning for NYC Businesses | TheCleanHandy",
        "meta_description": "Office, retail, and recurring cleaning for New York City businesses, quoted from the space and the schedule.",
        "introduction": "Cleaning programs for offices, shops, and other businesses that need a checklist and a schedule.",
        "body": "Business quotes name the rooms, the days, and whether the crew comes after hours. Office, retail, and recurring commercial pages describe the checklists. A one-time reset before a new occupant is available, and it is priced as that visit rather than hidden inside a monthly plan you did not ask for.",
    },
    {
        "slug": "landlords",
        "name": "For Landlords",
        "seo_title": "Move-Out Cleaning for NYC Landlords | TheCleanHandy",
        "meta_description": "Landlord move-out and turnover cleaning in NYC so a unit can be inspected and re-rented.",
        "introduction": "Move-out and turnover cleaning for landlords taking an apartment back or preparing it for the next tenant.",
        "body": "The clean covers the checklist on the quote. It does not decide a security deposit. If the unit has damage, leftover furniture, or no water, the crew reports that and the price can change. Landlords with one unit can book as a customer. Landlords with several units can use a property-manager account.",
    },
]


ARTICLES = [
    {
        "slug": "nyc-move-out-cleaning-checklist",
        "title": "NYC Move-Out Cleaning Checklist",
        "service": "move-out-cleaning-nyc",
        "seo_title": "NYC Move-Out Cleaning Checklist | TheCleanHandy",
        "meta_description": "A practical checklist for cleaning an NYC apartment before you return the keys.",
        "introduction": "Use this list after the furniture is out and before the landlord walks the apartment.",
        "body": "Empty the fridge and oven if you want their interiors cleaned. A crew cannot detail an appliance that is still full.\n- Wipe cabinet shelves and fronts\n- Clean the sink, counters, and appliance exteriors\n- Scrub the bathroom fixtures, tub or shower, and floor\n- Vacuum or mop every room on the lease\n- Dust baseboards, doors, and windowsills\n- Clean interior window glass\n- Remove cobwebs from corners and closet ceilings\nTell the building the date. In a walk-up, the floor number belongs on the quote so the cleaners plan the carry.",
    },
    {
        "slug": "move-in-cleaning-checklist",
        "title": "Move-In Cleaning Checklist",
        "service": "move-in-cleaning-nyc",
        "seo_title": "Move-In Cleaning Checklist | TheCleanHandy",
        "meta_description": "What to clean in a new NYC apartment before the furniture comes in.",
        "introduction": "Move-in cleaning is easier in an empty apartment. Book it for a day you have the keys and before the truck.",
        "body": "Walk the unit once and note paint dust. If the dust is from a renovation, ask for post-renovation cleaning instead of a standard move-in.\n- Wipe empty cabinets and drawers\n- Clean bathroom fixtures before towels are hung\n- Wash floors while they are clear\n- Clean interior windows\n- Wipe switches and handles\n- Check that appliances are empty before requesting interiors\nAfter the clean, the moving crew can place furniture. Combining both is a single quote if you want TheCleanHandy to do each part.",
    },
    {
        "slug": "office-cleaning-checklist",
        "title": "Office Cleaning Checklist",
        "service": "office-cleaning-nyc",
        "seo_title": "Office Cleaning Checklist | TheCleanHandy",
        "meta_description": "What a recurring NYC office clean covers, and what should be written into the quote.",
        "introduction": "An office clean is a repeating checklist. The quote should say which rooms and which days.",
        "body": "Decide whether the crew arrives after staff leave. After-hours access, alarms, and keys belong in the request.\n- Wipe desks, tables, and conference surfaces\n- Sanitize handles and switches\n- Empty trash and replace liners\n- Vacuum or mop floors\n- Clean and restock restrooms with supplies you provide\n- Wipe kitchenette counters and appliance exteriors\nA weekly office and a five-day office are different quotes. The residential time guide does not set the commercial price.",
    },
]


FAQS = [
    ("How much does move-out cleaning cost in NYC?", "TheCleanHandy does not publish a dollar price for move-out cleaning. The published time guide for a 1,000–1,500 sq ft move-in/out is 2 cleaners for about 5 hours. The written quote uses your size, condition, and access.", "move-out-cleaning-nyc", True),
    ("What is included in a NYC move-out cleaning?", "Kitchens, bathrooms, floors, interior cabinets, appliance exteriors, interior windows, and dust on baseboards and doors. Interiors of the fridge and oven are included when they are empty and listed on the quote.", "move-out-cleaning-nyc", True),
    ("Should I clean my apartment before moving out?", "If the lease or the landlord expects a clean handoff, a move-out clean is the visit for that. Furniture should be out first when you can arrange it.", "move-out-cleaning-nyc", False),
    ("How long does move-out cleaning take?", "For 1,000–1,500 sq ft, the published guide is about 5 hours with 2 cleaners. Larger bands on the pricing page use more cleaners or more hours. Condition can change the quote.", "move-out-cleaning-nyc", True),
    ("What should I clean before handing an apartment back to my landlord?", "Kitchen, bathrooms, floors, cabinets, and interior glass are the usual inspection items. The move-out checklist on this site is the practical list. The deposit decision stays with the landlord.", "move-out-cleaning-nyc", False),
    ("What happens before I move furniture into a new apartment?", "Move-in cleaning is done in the empty apartment: cabinets, baths, floors, and interior glass, so you unpack onto clean surfaces.", "move-in-cleaning-nyc", False),
    ("Can I book cleaning and moving services together?", "Yes. Use Moving and Cleaning, or describe both jobs in one quote request. The estimate separates the crew work from the cleaning checklist.", "moving-and-cleaning-nyc", True),
    ("What does a commercial cleaning company do?", "On a TheCleanHandy commercial visit: restrooms, floors, trash, high-touch surfaces, and the break area or sales floor named in the quote.", "commercial-cleaning-nyc", True),
    ("How often should an NYC office be professionally cleaned?", "That depends on headcount and how the space is used. Many offices choose weekly or several days a week. The quote names the rhythm instead of assuming one.", "office-cleaning-nyc", True),
    ("Do you bring a truck?", "A truck or van is listed on moving pages only when that capability is turned on in the company profile. If it is off, the quote covers crew labor and will not claim a truck.", "moving-services-nyc", False),
    ("Which areas do you serve?", "Manhattan, Brooklyn, Queens, the Bronx, Staten Island, Astoria, Long Island, and New Jersey.", "", True),
]


PRICING = [
    ("Post-Renovation Cleaning", "post-renovation-cleaning-nyc", [("1,000–1,500 sq ft", 3, 6), ("1,500–2,000 sq ft", 3, 8), ("2,000–2,500 sq ft", 4, 8), ("2,500–3,000 sq ft", 5, 8)]),
    ("Deep Cleaning", "deep-cleaning-nyc", [("1,000–1,500 sq ft", 2, 5), ("1,500–2,000 sq ft", 3, 5), ("2,000–2,500 sq ft", 3, 7), ("2,500–3,000 sq ft", 3, 8)]),
    ("Move In / Move Out", "move-in-out-cleaning-nyc", [("1,000–1,500 sq ft", 2, 5), ("1,500–2,000 sq ft", 3, 5), ("2,000–2,500 sq ft", 3, 7), ("2,500–3,000 sq ft", 3, 8)]),
    ("Regular Cleaning", "", [("1,000–1,500 sq ft", 2, 3), ("1,500–2,000 sq ft", 2, 5), ("2,000–2,500 sq ft", 2, 7), ("2,500–3,000 sq ft", 2, 8)]),
]


REDIRECTS = [
    ("/quotes/faq", "/faq/"),
    ("/quotes/faq/", "/faq/"),
    ("/quotes/terms", "/terms/"),
    ("/quotes/terms/", "/terms/"),
    ("/quotes/privacy", "/privacy/"),
    ("/quotes/privacy/", "/privacy/"),
    ("/quotes/cleaning/request/4", "/move-in-out-cleaning-nyc/"),
    ("/quotes/cleaning/request/4/", "/move-in-out-cleaning-nyc/"),
    ("/quotes/cleaning/request/6", "/office-cleaning-nyc/"),
    ("/quotes/cleaning/request/6/", "/office-cleaning-nyc/"),
]


RELATIONS = {
    "moving-services-nyc": ["apartment-moving-nyc", "small-moves-nyc", "moving-labor-nyc", "moving-and-cleaning-nyc"],
    "apartment-moving-nyc": ["moving-services-nyc", "moving-and-cleaning-nyc", "move-out-cleaning-nyc"],
    "small-moves-nyc": ["moving-services-nyc", "moving-labor-nyc"],
    "moving-labor-nyc": ["moving-services-nyc", "small-moves-nyc"],
    "moving-and-cleaning-nyc": ["moving-services-nyc", "move-out-cleaning-nyc", "move-in-cleaning-nyc"],
    "move-in-out-cleaning-nyc": ["move-out-cleaning-nyc", "move-in-cleaning-nyc", "apartment-move-out-cleaning-nyc", "rental-turnover-cleaning-nyc"],
    "move-out-cleaning-nyc": ["move-in-out-cleaning-nyc", "apartment-move-out-cleaning-nyc", "rental-turnover-cleaning-nyc", "moving-and-cleaning-nyc"],
    "move-in-cleaning-nyc": ["move-in-out-cleaning-nyc", "deep-cleaning-nyc", "moving-and-cleaning-nyc"],
    "apartment-move-out-cleaning-nyc": ["move-out-cleaning-nyc", "rental-turnover-cleaning-nyc"],
    "rental-turnover-cleaning-nyc": ["move-out-cleaning-nyc", "move-in-cleaning-nyc", "property-management-cleaning"],
    "deep-cleaning-nyc": ["move-in-cleaning-nyc", "move-out-cleaning-nyc"],
    "post-renovation-cleaning-nyc": ["deep-cleaning-nyc", "move-in-cleaning-nyc"],
    "commercial-cleaning-nyc": ["office-cleaning-nyc", "retail-cleaning-nyc", "property-management-cleaning", "recurring-commercial-cleaning"],
    "office-cleaning-nyc": ["commercial-cleaning-nyc", "recurring-commercial-cleaning"],
    "retail-cleaning-nyc": ["commercial-cleaning-nyc", "recurring-commercial-cleaning"],
    "property-management-cleaning": ["rental-turnover-cleaning-nyc", "commercial-cleaning-nyc", "recurring-commercial-cleaning"],
    "recurring-commercial-cleaning": ["office-cleaning-nyc", "commercial-cleaning-nyc"],
    "additional-services": ["assembly", "mounting", "painting", "post-event-cleaning-nyc"],
    "assembly": ["additional-services", "moving-services-nyc"],
    "mounting": ["additional-services"],
    "painting": ["additional-services", "post-renovation-cleaning-nyc"],
    "post-event-cleaning-nyc": ["additional-services", "deep-cleaning-nyc"],
}

SOLUTION_LINKS = {
    "property-managers": ["rental-turnover-cleaning-nyc", "move-out-cleaning-nyc", "move-in-cleaning-nyc", "property-management-cleaning", "recurring-commercial-cleaning"],
    "businesses": ["commercial-cleaning-nyc", "office-cleaning-nyc", "retail-cleaning-nyc", "recurring-commercial-cleaning"],
    "landlords": ["move-out-cleaning-nyc", "rental-turnover-cleaning-nyc", "move-in-cleaning-nyc", "apartment-move-out-cleaning-nyc"],
}

AREA_SLUGS = ["manhattan", "brooklyn", "queens", "bronx", "astoria", "staten-island", "long-island", "new-jersey"]
PRIMARY_AREA_SERVICES = [
    "moving-services-nyc",
    "move-out-cleaning-nyc",
    "move-in-cleaning-nyc",
    "commercial-cleaning-nyc",
    "office-cleaning-nyc",
    "rental-turnover-cleaning-nyc",
]


class Command(BaseCommand):
    help = "Seed company facts, service pages, areas, guides, pricing, and legacy redirects."

    def handle(self, *args, **options):
        CompanyProfile.objects.update_or_create(
            pk=1,
            defaults={
                "legal_name": "TheCleanHandy",
                "phone": "(347) 652-6165",
                "public_email": "support@thecleanhandy.com",
                "info_email": "info@thecleanhandy.com",
                "website": "https://thecleanhandy.com",
                "service_area": "New York City, Long Island, and New Jersey",
                "street_address": "",
                "city": "Astoria",
                "region": "NY",
                "postal_code": "11106",
                "hours": "By appointment",
                "about": ABOUT,
                "provides_truck": False,
                "provides_packing": False,
                "provides_insurance": False,
            },
        )
        pages = {}
        for raw in SERVICES:
            row = dict(raw)
            bookable = row.pop("bookable")
            slug = row.pop("slug")
            pages[slug], _ = ServicePage.objects.update_or_create(
                slug=slug,
                defaults={**row, "is_bookable": bookable, "is_active": True, "canonical_path": f"/{slug}/"},
            )
        areas = {}
        for row in LOCATIONS:
            areas[row["slug"]], _ = LocationPage.objects.update_or_create(
                slug=row["slug"],
                defaults={**row, "canonical_path": f"/areas/{row['slug']}/"},
            )
        solutions = {}
        for row in SOLUTIONS:
            solutions[row["slug"]], _ = SolutionPage.objects.update_or_create(
                slug=row["slug"],
                defaults={**row, "canonical_path": f"/solutions/{row['slug']}/"},
            )
        for slug, related in RELATIONS.items():
            pages[slug].related_services.set([pages[item] for item in related])
        for slug in pages:
            if slug in PRIMARY_AREA_SERVICES or pages[slug].category in {"moving", "move_cleaning", "commercial"}:
                pages[slug].locations.set(areas.values())
        for slug, linked in SOLUTION_LINKS.items():
            for service_slug in linked:
                pages[service_slug].solutions.add(solutions[slug])
        for raw in ARTICLES:
            row = dict(raw)
            service = pages[row.pop("service")]
            slug = row["slug"]
            Article.objects.update_or_create(
                slug=slug,
                defaults={**row, "service": service, "canonical_path": f"/resources/{slug}/"},
            )
        FAQ.objects.all().delete()
        for order, (question, answer, service_slug, on_home) in enumerate(FAQS):
            FAQ.objects.create(
                question=question,
                answer=answer,
                service=pages.get(service_slug),
                show_on_homepage=on_home,
                order=order,
            )
        PricingGuideRow.objects.all().delete()
        sort_order = 0
        for label, service_slug, bands in PRICING:
            for band, cleaners, hours in bands:
                PricingGuideRow.objects.create(
                    service=pages.get(service_slug),
                    label=label,
                    sqft_band=band,
                    cleaners=cleaners,
                    hours=hours,
                    sort_order=sort_order,
                )
                sort_order += 1
        for source, target in REDIRECTS:
            LegacyRedirect.objects.update_or_create(
                from_path=source,
                defaults={"to_path": target, "status_code": 301},
            )
        seed_quote_prices()
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(pages)} services, {len(areas)} areas, {len(solutions)} solutions."))
