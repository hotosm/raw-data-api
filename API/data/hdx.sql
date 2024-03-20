CREATE TABLE if not exists public.hdx (
    id SERIAL PRIMARY KEY,
    iso3 VARCHAR(3) NULL,
    cid INT NULL,
    hdx_upload BOOLEAN DEFAULT true,
    dataset JSONB,
    queue VARCHAR DEFAULT 'raw_ondemand',
    meta BOOLEAN DEFAULT false,
    categories JSONB NULL,
    geometry public.geometry(MultiPolygon, 4326) NULL
);
CREATE INDEX if not exists hdx_dataset_idx ON public.hdx (dataset);

INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('AFG',168,true,'{"dataset_title": "Afghanistan", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_afg", "dataset_locations": ["afg"]}','raw_ondemand',false,NULL,NULL),
	 ('AND',108,true,'{"dataset_title": "Andorra", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_and", "dataset_locations": ["and"]}','raw_ondemand',false,NULL,NULL),
	 ('ALB',170,true,'{"dataset_title": "Albania", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_alb", "dataset_locations": ["alb"]}','raw_ondemand',false,NULL,NULL),
	 ('DZA',100,true,'{"dataset_title": "Algeria", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_dza", "dataset_locations": ["dza"]}','raw_ondemand',false,NULL,NULL),
	 ('AGO',171,true,'{"dataset_title": "Angola", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_ago", "dataset_locations": ["ago"]}','raw_ondemand',false,NULL,NULL),
	 ('AIA',37,true,'{"dataset_title": "Anguilla", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_aia", "dataset_locations": ["aia"]}','raw_ondemand',false,NULL,NULL),
	 ('ATA',66,true,'{"dataset_title": "Antarctica", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_ata", "dataset_locations": ["ata"]}','raw_ondemand',false,NULL,NULL),
	 ('ATG',57,true,'{"dataset_title": "Antigua and Barbuda", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_atg", "dataset_locations": ["atg"]}','raw_ondemand',false,NULL,NULL),
	 ('AZE',166,true,'{"dataset_title": "Azerbaijan", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_aze", "dataset_locations": ["aze"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('BHS',4,true,'{"dataset_title": "Bahamas", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_bhs", "dataset_locations": ["bhs"]}','raw_ondemand',false,NULL,NULL),
	 ('BHR',2,true,'{"dataset_title": "Bahrain", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_bhr", "dataset_locations": ["bhr"]}','raw_ondemand',false,NULL,NULL),
	 ('VGB',42,true,'{"dataset_title": "British Virgin Islands", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_vgb", "dataset_locations": ["vgb"]}','raw_ondemand',false,NULL,NULL),
	 ('ARG',172,true,'{"dataset_title": "Argentina", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_arg", "dataset_locations": ["arg"]}','raw_ondemand',false,NULL,NULL),
	 ('BLZ',43,true,'{"dataset_title": "Belize", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_blz", "dataset_locations": ["blz"]}','raw_ondemand',false,NULL,NULL),
	 ('BEN',87,true,'{"dataset_title": "Benin", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_ben", "dataset_locations": ["ben"]}','raw_ondemand',false,NULL,NULL),
	 ('BMU',29,true,'{"dataset_title": "Bermuda", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_bmu", "dataset_locations": ["bmu"]}','raw_ondemand',false,NULL,NULL),
	 ('ARM',174,true,'{"dataset_title": "Armenia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_arm", "dataset_locations": ["arm"]}','raw_ondemand',false,NULL,NULL),
	 ('ABW',68,true,'{"dataset_title": "Aruba", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_abw", "dataset_locations": ["abw"]}','raw_ondemand',false,NULL,NULL),
	 ('AUS',56,true,'{"dataset_title": "Australia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_aus", "dataset_locations": ["aus"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('CMR',91,true,'{"dataset_title": "Cameroon", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_cmr", "dataset_locations": ["cmr"]}','raw_ondemand',false,NULL,NULL),
	 ('AUT',176,true,'{"dataset_title": "Austria", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_aut", "dataset_locations": ["aut"]}','raw_ondemand',false,NULL,NULL),
	 ('PSE',107,true,'{"dataset_title": "State of Palestine", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_pse", "dataset_locations": ["pse"]}','raw_ondemand',false,NULL,NULL),
	 ('TON',24,true,'{"dataset_title": "Tonga", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_ton", "dataset_locations": ["ton"]}','raw_ondemand',false,NULL,NULL),
	 ('BGD',54,true,'{"dataset_title": "Bangladesh", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_bgd", "dataset_locations": ["bgd"]}','raw_ondemand',false,NULL,NULL),
	 ('TCD',53,true,'{"dataset_title": "Chad", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_tcd", "dataset_locations": ["tcd"]}','raw_ondemand',false,NULL,NULL),
	 ('IDN',118,true,'{"dataset_title": "Indonesia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_idn", "dataset_locations": ["idn"]}','raw_ondemand',false,NULL,NULL),
	 ('BRB',69,true,'{"dataset_title": "Barbados", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_brb", "dataset_locations": ["brb"]}','raw_ondemand',false,NULL,NULL),
	 ('GIN',39,true,'{"dataset_title": "Guinea", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_gin", "dataset_locations": ["gin"]}','raw_ondemand',false,NULL,NULL),
	 ('BLR',180,true,'{"dataset_title": "Belarus", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_blr", "dataset_locations": ["blr"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('GNB',188,true,'{"dataset_title": "Guinea Bissau", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_gnb", "dataset_locations": ["gnb"]}','raw_ondemand',false,NULL,NULL),
	 ('TTO',12,true,'{"dataset_title": "Trinidad and Tobago", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_tto", "dataset_locations": ["tto"]}','raw_ondemand',false,NULL,NULL),
	 ('BEL',182,true,'{"dataset_title": "Belgium", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_bel", "dataset_locations": ["bel"]}','raw_ondemand',false,NULL,NULL),
	 ('BTN',167,true,'{"dataset_title": "Bhutan", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_btn", "dataset_locations": ["btn"]}','raw_ondemand',false,NULL,NULL),
	 ('BOL',3,true,'{"dataset_title": "Bolivia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_bol", "dataset_locations": ["bol"]}','raw_ondemand',false,NULL,NULL),
	 ('BES',58,true,'{"dataset_title": "Bonaire, Sint Eustatius and Saba", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_bes", "dataset_locations": ["bes"]}','raw_ondemand',false,NULL,NULL),
	 ('BRA',77,true,'{"dataset_title": "Brazil", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_bra", "dataset_locations": ["bra"]}','raw_ondemand',false,NULL,NULL),
	 ('IOT',30,true,'{"dataset_title": "British Indian Ocean Territory", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_iot", "dataset_locations": ["iot"]}','raw_ondemand',false,NULL,NULL),
	 ('BIH',187,true,'{"dataset_title": "Bosnia and Herzegovina", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_bih", "dataset_locations": ["bih"]}','raw_ondemand',false,NULL,NULL),
	 ('PER',156,true,'{"dataset_title": "Peru", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_per", "dataset_locations": ["per"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('BWA',189,true,'{"dataset_title": "Botswana", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_bwa", "dataset_locations": ["bwa"]}','raw_ondemand',false,NULL,NULL),
	 ('BVT',38,true,'{"dataset_title": "Bouvet Island", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_bvt", "dataset_locations": ["bvt"]}','raw_ondemand',false,NULL,NULL),
	 ('PHL',183,true,'{"dataset_title": "Philippines", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_phl", "dataset_locations": ["phl"]}','raw_ondemand',false,NULL,NULL),
	 ('PCN',121,true,'{"dataset_title": "Pitcairn Islands", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_pcn", "dataset_locations": ["pcn"]}','raw_ondemand',false,NULL,NULL),
	 ('BRN',227,true,'{"dataset_title": "Brunei Darussalam", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_brn", "dataset_locations": ["brn"]}','raw_ondemand',false,NULL,NULL),
	 ('QAT',228,true,'{"dataset_title": "Qatar", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_qat", "dataset_locations": ["qat"]}','raw_ondemand',false,NULL,NULL),
	 ('REU',6,true,'{"dataset_title": "Reunion", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_reu", "dataset_locations": ["reu"]}','raw_ondemand',false,NULL,NULL),
	 ('BGR',191,true,'{"dataset_title": "Bulgaria", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_bgr", "dataset_locations": ["bgr"]}','raw_ondemand',false,NULL,NULL),
	 ('CHL',217,true,'{"dataset_title": "Chile", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_chl", "dataset_locations": ["chl"]}','raw_ondemand',false,NULL,NULL),
	 ('VCT',19,true,'{"dataset_title": "Saint Vincent And The Grenadines", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_vct", "dataset_locations": ["vct"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('WSM',13,true,'{"dataset_title": "Samoa", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_wsm", "dataset_locations": ["wsm"]}','raw_ondemand',false,NULL,NULL),
	 ('BFA',195,true,'{"dataset_title": "Burkina Faso", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_bfa", "dataset_locations": ["bfa"]}','raw_ondemand',false,NULL,NULL),
	 ('DOM',164,true,'{"dataset_title": "Dominican Republic", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_dom", "dataset_locations": ["dom"]}','raw_ondemand',false,NULL,NULL),
	 ('BDI',197,true,'{"dataset_title": "Burundi", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_bdi", "dataset_locations": ["bdi"]}','raw_ondemand',false,NULL,NULL),
	 ('CPV',27,true,'{"dataset_title": "Cabo Verde", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_cpv", "dataset_locations": ["cpv"]}','raw_ondemand',false,NULL,NULL),
	 ('KHM',198,true,'{"dataset_title": "Cambodia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_khm", "dataset_locations": ["khm"]}','raw_ondemand',false,NULL,NULL),
	 ('CAN',59,true,'{"dataset_title": "Canada", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_can", "dataset_locations": ["can"]}','raw_ondemand',false,NULL,NULL),
	 ('CYM',34,true,'{"dataset_title": "Cayman Islands", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_cym", "dataset_locations": ["cym"]}','raw_ondemand',false,NULL,NULL),
	 ('CAF',106,true,'{"dataset_title": "Central African Republic", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_caf", "dataset_locations": ["caf"]}','raw_ondemand',false,NULL,NULL),
	 ('GUF',65,true,'{"dataset_title": "French Guiana", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_guf", "dataset_locations": ["guf"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('CHN',63,true,'{"dataset_title": "China", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_chn", "dataset_locations": ["chn"]}','raw_ondemand',false,NULL,NULL),
	 ('PYF',10,true,'{"dataset_title": "French Polynesia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_pyf", "dataset_locations": ["pyf"]}','raw_ondemand',false,NULL,NULL),
	 ('HKG',76,true,'{"dataset_title": "China, Hong Kong Special Administrative Region", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_hkg", "dataset_locations": ["hkg"]}','raw_ondemand',false,NULL,NULL),
	 ('MAC',61,true,'{"dataset_title": "China, Macao Special Administrative Region", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_mac", "dataset_locations": ["mac"]}','raw_ondemand',false,NULL,NULL),
	 ('ATF',179,true,'{"dataset_title": "French Southern and Antarctic Territories", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_atf", "dataset_locations": ["atf"]}','raw_ondemand',false,NULL,NULL),
	 ('COL',194,true,'{"dataset_title": "Colombia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_col", "dataset_locations": ["col"]}','raw_ondemand',false,NULL,NULL),
	 ('COM',28,true,'{"dataset_title": "Comoros", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_com", "dataset_locations": ["com"]}','raw_ondemand',false,NULL,NULL),
	 ('COG',131,true,'{"dataset_title": "Congo", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_cog", "dataset_locations": ["cog"]}','raw_ondemand',false,NULL,NULL),
	 ('COK',109,true,'{"dataset_title": "Cook Islands", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_cok", "dataset_locations": ["cok"]}','raw_ondemand',false,NULL,NULL),
	 ('CRI',196,true,'{"dataset_title": "Costa Rica", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_cri", "dataset_locations": ["cri"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('CIV',221,true,'{"dataset_title": "Côte d''Ivoire", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_civ", "dataset_locations": ["civ"]}','raw_ondemand',false,NULL,NULL),
	 ('HRV',67,true,'{"dataset_title": "Croatia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_hrv", "dataset_locations": ["hrv"]}','raw_ondemand',false,NULL,NULL),
	 ('CUB',149,true,'{"dataset_title": "Cuba", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_cub", "dataset_locations": ["cub"]}','raw_ondemand',false,NULL,NULL),
	 ('CUW',44,true,'{"dataset_title": "Curaçao", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_cuw", "dataset_locations": ["cuw"]}','raw_ondemand',false,NULL,NULL),
	 ('CYP',128,true,'{"dataset_title": "Cyprus", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_cyp", "dataset_locations": ["cyp"]}','raw_ondemand',false,NULL,NULL),
	 ('CZE',199,true,'{"dataset_title": "Czech Republic", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_cze", "dataset_locations": ["cze"]}','raw_ondemand',false,NULL,NULL),
	 ('GAB',82,true,'{"dataset_title": "Gabon", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_gab", "dataset_locations": ["gab"]}','raw_ondemand',false,NULL,NULL),
	 ('COD',89,true,'{"dataset_title": "Democratic Republic of the Congo", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_cod", "dataset_locations": ["cod"]}','raw_ondemand',false,NULL,NULL),
	 ('DNK',16,true,'{"dataset_title": "Denmark", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_dnk", "dataset_locations": ["dnk"]}','raw_ondemand',false,NULL,NULL),
	 ('DJI',48,true,'{"dataset_title": "Djibouti", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_dji", "dataset_locations": ["dji"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('DMA',33,true,'{"dataset_title": "Dominica", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_dma", "dataset_locations": ["dma"]}','raw_ondemand',false,NULL,NULL),
	 ('GMB',207,true,'{"dataset_title": "Gambia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_gmb", "dataset_locations": ["gmb"]}','raw_ondemand',false,NULL,NULL),
	 ('ECU',200,true,'{"dataset_title": "Ecuador", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_ecu", "dataset_locations": ["ecu"]}','raw_ondemand',false,NULL,NULL),
	 ('EGY',79,true,'{"dataset_title": "Egypt", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_egy", "dataset_locations": ["egy"]}','raw_ondemand',false,NULL,NULL),
	 ('SLV',74,true,'{"dataset_title": "El Salvador", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_slv", "dataset_locations": ["slv"]}','raw_ondemand',false,NULL,NULL),
	 ('GNQ',138,true,'{"dataset_title": "Equatorial Guinea", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_gnq", "dataset_locations": ["gnq"]}','raw_ondemand',false,NULL,NULL),
	 ('ERI',117,true,'{"dataset_title": "Eritrea", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_eri", "dataset_locations": ["eri"]}','raw_ondemand',false,NULL,NULL),
	 ('GEO',1,true,'{"dataset_title": "Georgia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_geo", "dataset_locations": ["geo"]}','raw_ondemand',false,NULL,NULL),
	 ('DEU',50,true,'{"dataset_title": "Germany", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_deu", "dataset_locations": ["deu"]}','raw_ondemand',false,NULL,NULL),
	 ('EST',201,true,'{"dataset_title": "Estonia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_est", "dataset_locations": ["est"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('SWZ',144,true,'{"dataset_title": "Eswatini", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_swz", "dataset_locations": ["swz"]}','raw_ondemand',false,NULL,NULL),
	 ('ETH',75,true,'{"dataset_title": "Ethiopia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_eth", "dataset_locations": ["eth"]}','raw_ondemand',false,NULL,NULL),
	 ('FLK',165,true,'{"dataset_title": "Falkland Islands ( Malvinas)", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_flk", "dataset_locations": ["flk"]}','raw_ondemand',false,NULL,NULL),
	 ('FRO',70,true,'{"dataset_title": "Faroe Islands", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_fro", "dataset_locations": ["fro"]}','raw_ondemand',false,NULL,NULL),
	 ('FJI',150,true,'{"dataset_title": "Fiji", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_fji", "dataset_locations": ["fji"]}','raw_ondemand',false,NULL,NULL),
	 ('FIN',119,true,'{"dataset_title": "Finland", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_fin", "dataset_locations": ["fin"]}','raw_ondemand',false,NULL,NULL),
	 ('GHA',40,true,'{"dataset_title": "Ghana", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_gha", "dataset_locations": ["gha"]}','raw_ondemand',false,NULL,NULL),
	 ('HTI',210,true,'{"dataset_title": "Haiti", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_hti", "dataset_locations": ["hti"]}','raw_ondemand',false,NULL,NULL),
	 ('VAT',55,true,'{"dataset_title": "Holy See (Vatican City State)", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_vat", "dataset_locations": ["vat"]}','raw_ondemand',false,NULL,NULL),
	 ('HND',169,true,'{"dataset_title": "Honduras", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_hnd", "dataset_locations": ["hnd"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('HUN',14,true,'{"dataset_title": "Hungary", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_hun", "dataset_locations": ["hun"]}','raw_ondemand',false,NULL,NULL),
	 ('FRA',226,true,'{"dataset_title": "France", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_fra", "dataset_locations": ["fra"]}','raw_ondemand',false,NULL,NULL),
	 ('GRC',202,true,'{"dataset_title": "Greece", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_grc", "dataset_locations": ["grc"]}','raw_ondemand',false,NULL,NULL),
	 ('GRL',45,true,'{"dataset_title": "Greenland", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_grl", "dataset_locations": ["grl"]}','raw_ondemand',false,NULL,NULL),
	 ('GRD',93,true,'{"dataset_title": "Grenada", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_grd", "dataset_locations": ["grd"]}','raw_ondemand',false,NULL,NULL),
	 ('GLP',62,true,'{"dataset_title": "Guadeloupe", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_glp", "dataset_locations": ["glp"]}','raw_ondemand',false,NULL,NULL),
	 ('ISL',41,true,'{"dataset_title": "Iceland", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_isl", "dataset_locations": ["isl"]}','raw_ondemand',false,NULL,NULL),
	 ('IND',7,true,'{"dataset_title": "India", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_ind", "dataset_locations": ["ind"]}','raw_ondemand',false,NULL,NULL),
	 ('GTM',203,true,'{"dataset_title": "Guatemala", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_gtm", "dataset_locations": ["gtm"]}','raw_ondemand',false,NULL,NULL),
	 ('GGY',83,true,'{"dataset_title": "Guernsey", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_ggy", "dataset_locations": ["ggy"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('GUY',94,true,'{"dataset_title": "Guyana", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_guy", "dataset_locations": ["guy"]}','raw_ondemand',false,NULL,NULL),
	 ('IRN',204,true,'{"dataset_title": "Iran", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_irn", "dataset_locations": ["irn"]}','raw_ondemand',false,NULL,NULL),
	 ('ITA',123,true,'{"dataset_title": "Italy", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_ita", "dataset_locations": ["ita"]}','raw_ondemand',false,NULL,NULL),
	 ('JAM',26,true,'{"dataset_title": "Jamaica", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_jam", "dataset_locations": ["jam"]}','raw_ondemand',false,NULL,NULL),
	 ('JPN',22,true,'{"dataset_title": "Japan", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_jpn", "dataset_locations": ["jpn"]}','raw_ondemand',false,NULL,NULL),
	 ('IRQ',238,true,'{"dataset_title": "Iraq", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_irq", "dataset_locations": ["irq"]}','raw_ondemand',false,NULL,NULL),
	 ('IRL',98,true,'{"dataset_title": "Ireland And Northern Ireland", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_irl", "dataset_locations": ["irl"]}','raw_ondemand',false,NULL,NULL),
	 ('IMN',125,true,'{"dataset_title": "Isle Of Man", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_imn", "dataset_locations": ["imn"]}','raw_ondemand',false,NULL,NULL),
	 ('ISR',185,true,'{"dataset_title": "Israel", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_isr", "dataset_locations": ["isr"]}','raw_ondemand',false,NULL,NULL),
	 ('JEY',84,true,'{"dataset_title": "Jersey", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_jey", "dataset_locations": ["jey"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('JOR',239,true,'{"dataset_title": "Jordan", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_jor", "dataset_locations": ["jor"]}','raw_ondemand',false,NULL,NULL),
	 ('KEN',141,true,'{"dataset_title": "Kenya", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_ken", "dataset_locations": ["ken"]}','raw_ondemand',false,NULL,NULL),
	 ('KIR',46,true,'{"dataset_title": "Kiribati", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_kir", "dataset_locations": ["kir"]}','raw_ondemand',false,NULL,NULL),
	 ('KAZ',233,true,'{"dataset_title": "Kazakhstan", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_kaz", "dataset_locations": ["kaz"]}','raw_ondemand',false,NULL,NULL),
	 ('XKX',159,true,'{"dataset_title": "Kosovo", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_xkx", "dataset_locations": ["xkx"]}','raw_ondemand',false,NULL,NULL),
	 ('KWT',225,true,'{"dataset_title": "Kuwait", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_kwt", "dataset_locations": ["kwt"]}','raw_ondemand',false,NULL,NULL),
	 ('KGZ',11,true,'{"dataset_title": "Kyrgyzstan", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_kgz", "dataset_locations": ["kgz"]}','raw_ondemand',false,NULL,NULL),
	 ('LVA',175,true,'{"dataset_title": "Latvia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_lva", "dataset_locations": ["lva"]}','raw_ondemand',false,NULL,NULL),
	 ('LAO',78,true,'{"dataset_title": "Laos", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_lao", "dataset_locations": ["lao"]}','raw_ondemand',false,NULL,NULL),
	 ('LBY',153,true,'{"dataset_title": "Libya", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_lby", "dataset_locations": ["lby"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('LBN',208,true,'{"dataset_title": "Lebanon", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_lbn", "dataset_locations": ["lbn"]}','raw_ondemand',false,NULL,NULL),
	 ('LSO',192,true,'{"dataset_title": "Lesotho", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_lso", "dataset_locations": ["lso"]}','raw_ondemand',false,NULL,NULL),
	 ('LBR',148,true,'{"dataset_title": "Liberia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_lbr", "dataset_locations": ["lbr"]}','raw_ondemand',false,NULL,NULL),
	 ('LIE',173,true,'{"dataset_title": "Liechtenstein", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_lie", "dataset_locations": ["lie"]}','raw_ondemand',false,NULL,NULL),
	 ('LTU',209,true,'{"dataset_title": "Lithuania", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_ltu", "dataset_locations": ["ltu"]}','raw_ondemand',false,NULL,NULL),
	 ('LUX',81,true,'{"dataset_title": "Luxembourg", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_lux", "dataset_locations": ["lux"]}','raw_ondemand',false,NULL,NULL),
	 ('MDG',72,true,'{"dataset_title": "Madagascar", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_mdg", "dataset_locations": ["mdg"]}','raw_ondemand',false,NULL,NULL),
	 ('MNE',214,true,'{"dataset_title": "Montenegro", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_mne", "dataset_locations": ["mne"]}','raw_ondemand',false,NULL,NULL),
	 ('MWI',211,true,'{"dataset_title": "Malawi", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_mwi", "dataset_locations": ["mwi"]}','raw_ondemand',false,NULL,NULL),
	 ('NZL',129,true,'{"dataset_title": "New Zealand", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_nzl", "dataset_locations": ["nzl"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('MYS',230,true,'{"dataset_title": "Malaysia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_mys", "dataset_locations": ["mys"]}','raw_ondemand',false,NULL,NULL),
	 ('MDV',23,true,'{"dataset_title": "Maldives", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_mdv", "dataset_locations": ["mdv"]}','raw_ondemand',false,NULL,NULL),
	 ('MLI',158,true,'{"dataset_title": "Mali", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_mli", "dataset_locations": ["mli"]}','raw_ondemand',false,NULL,NULL),
	 ('MLT',71,true,'{"dataset_title": "Malta", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_mlt", "dataset_locations": ["mlt"]}','raw_ondemand',false,NULL,NULL),
	 ('MHL',60,true,'{"dataset_title": "Marshall Islands", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_mhl", "dataset_locations": ["mhl"]}','raw_ondemand',false,NULL,NULL),
	 ('MTQ',49,true,'{"dataset_title": "Martinique", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_mtq", "dataset_locations": ["mtq"]}','raw_ondemand',false,NULL,NULL),
	 ('MRT',152,true,'{"dataset_title": "Mauritania", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_mrt", "dataset_locations": ["mrt"]}','raw_ondemand',false,NULL,NULL),
	 ('MUS',64,true,'{"dataset_title": "Mauritius", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_mus", "dataset_locations": ["mus"]}','raw_ondemand',false,NULL,NULL),
	 ('MYT',31,true,'{"dataset_title": "Mayotte", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_myt", "dataset_locations": ["myt"]}','raw_ondemand',false,NULL,NULL),
	 ('MEX',212,true,'{"dataset_title": "Mexico", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_mex", "dataset_locations": ["mex"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('FSM',47,true,'{"dataset_title": "Micronesia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_fsm", "dataset_locations": ["fsm"]}','raw_ondemand',false,NULL,NULL),
	 ('MDA',186,true,'{"dataset_title": "Moldova", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_mda", "dataset_locations": ["mda"]}','raw_ondemand',false,NULL,NULL),
	 ('MCO',213,true,'{"dataset_title": "Monaco", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_mco", "dataset_locations": ["mco"]}','raw_ondemand',false,NULL,NULL),
	 ('MNG',15,true,'{"dataset_title": "Mongolia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_mng", "dataset_locations": ["mng"]}','raw_ondemand',false,NULL,NULL),
	 ('MSR',97,true,'{"dataset_title": "Montserrat", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_msr", "dataset_locations": ["msr"]}','raw_ondemand',false,NULL,NULL),
	 ('MAR',178,true,'{"dataset_title": "Morocco", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_mar", "dataset_locations": ["mar"]}','raw_ondemand',false,NULL,NULL),
	 ('NIC',116,true,'{"dataset_title": "Nicaragua", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_nic", "dataset_locations": ["nic"]}','raw_ondemand',false,NULL,NULL),
	 ('MOZ',215,true,'{"dataset_title": "Mozambique", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_moz", "dataset_locations": ["moz"]}','raw_ondemand',false,NULL,NULL),
	 ('NER',90,true,'{"dataset_title": "Niger", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_ner", "dataset_locations": ["ner"]}','raw_ondemand',false,NULL,NULL),
	 ('PNG',133,true,'{"dataset_title": "Papua New Guinea", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_png", "dataset_locations": ["png"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('MMR',86,true,'{"dataset_title": "Myanmar", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_mmr", "dataset_locations": ["mmr"]}','raw_ondemand',false,NULL,NULL),
	 ('NAM',115,true,'{"dataset_title": "Namibia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_nam", "dataset_locations": ["nam"]}','raw_ondemand',false,NULL,NULL),
	 ('NRU',32,true,'{"dataset_title": "Nauru", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_nru", "dataset_locations": ["nru"]}','raw_ondemand',false,NULL,NULL),
	 ('PRY',127,true,'{"dataset_title": "Paraguay", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_pry", "dataset_locations": ["pry"]}','raw_ondemand',false,NULL,NULL),
	 ('NPL',73,true,'{"dataset_title": "Nepal", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_npl", "dataset_locations": ["npl"]}','raw_ondemand',false,NULL,NULL),
	 ('PRK',229,true,'{"dataset_title": "North Korea", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_prk", "dataset_locations": ["prk"]}','raw_ondemand',false,NULL,NULL),
	 ('NLD',92,true,'{"dataset_title": "Netherlands", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_nld", "dataset_locations": ["nld"]}','raw_ondemand',false,NULL,NULL),
	 ('NCL',120,true,'{"dataset_title": "New Caledonia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_ncl", "dataset_locations": ["ncl"]}','raw_ondemand',false,NULL,NULL),
	 ('NGA',151,true,'{"dataset_title": "Nigeria", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_nga", "dataset_locations": ["nga"]}','raw_ondemand',false,NULL,NULL),
	 ('NIU',17,true,'{"dataset_title": "Niue", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_niu", "dataset_locations": ["niu"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('PAN',155,true,'{"dataset_title": "Panama", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_pan", "dataset_locations": ["pan"]}','raw_ondemand',false,NULL,NULL),
	 ('MKD',206,true,'{"dataset_title": "North Macedonia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_mkd", "dataset_locations": ["mkd"]}','raw_ondemand',false,NULL,NULL),
	 ('NOR',154,true,'{"dataset_title": "Norway", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_nor", "dataset_locations": ["nor"]}','raw_ondemand',false,NULL,NULL),
	 (NULL,9,true,'{"dataset_title": "Nyiragongo volcanic eruption", "dataset_folder": "ISO3", "update_frequency": "disabled", "dataset_prefix": "hotosm_volcano_nyiragongo", "dataset_locations": ["cod"]}','raw_ondemand',false,NULL,NULL),
	 ('OMN',101,true,'{"dataset_title": "Oman", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_omn", "dataset_locations": ["omn"]}','raw_ondemand',false,NULL,NULL),
	 ('PAK',114,true,'{"dataset_title": "Pakistan", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_pak", "dataset_locations": ["pak"]}','raw_ondemand',false,NULL,NULL),
	 ('PLW',8,true,'{"dataset_title": "Palau", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_plw", "dataset_locations": ["plw"]}','raw_ondemand',false,NULL,NULL),
	 ('POL',157,true,'{"dataset_title": "Poland", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_pol", "dataset_locations": ["pol"]}','raw_ondemand',false,NULL,NULL),
	 ('PRT',161,true,'{"dataset_title": "Portugal", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_prt", "dataset_locations": ["prt"]}','raw_ondemand',false,NULL,NULL),
	 ('PRI',103,true,'{"dataset_title": "Puerto Rico", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_pri", "dataset_locations": ["pri"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('ROU',177,true,'{"dataset_title": "Romania", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_rou", "dataset_locations": ["rou"]}','raw_ondemand',false,NULL,NULL),
	 ('RUS',126,true,'{"dataset_title": "Russia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_rus", "dataset_locations": ["rus"]}','raw_ondemand',false,NULL,NULL),
	 ('RWA',181,true,'{"dataset_title": "Rwanda", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_rwa", "dataset_locations": ["rwa"]}','raw_ondemand',false,NULL,NULL),
	 ('BLM',104,true,'{"dataset_title": "Saint Barthélemy", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_blm", "dataset_locations": ["blm"]}','raw_ondemand',false,NULL,NULL),
	 ('SHN',52,true,'{"dataset_title": "Saint Helena, Ascension and Tristan da Cunha", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_shn", "dataset_locations": ["shn"]}','raw_ondemand',false,NULL,NULL),
	 ('KNA',99,true,'{"dataset_title": "Saint Kitts and Nevis", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_kna", "dataset_locations": ["kna"]}','raw_ondemand',false,NULL,NULL),
	 ('LCA',95,true,'{"dataset_title": "Saint Lucia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_lca", "dataset_locations": ["lca"]}','raw_ondemand',false,NULL,NULL),
	 (NULL,18,true,'{"dataset_title": "Saint Martin and Sint Maarten", "dataset_folder": "ISO3", "update_frequency": "disabled", "dataset_prefix": "hotosm_maf_sxm", "dataset_locations": ["maf", "sxm"]}','raw_ondemand',false,NULL,NULL),
	 ('SMR',105,true,'{"dataset_title": "San Marino", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_smr", "dataset_locations": ["smr"]}','raw_ondemand',false,NULL,NULL),
	 ('STP',51,true,'{"dataset_title": "Sao Tome And Principe", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_stp", "dataset_locations": ["stp"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('SLE',134,true,'{"dataset_title": "Sierra Leone", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_sle", "dataset_locations": ["sle"]}','raw_ondemand',false,NULL,NULL),
	 ('SAU',236,true,'{"dataset_title": "Saudi Arabia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_sau", "dataset_locations": ["sau"]}','raw_ondemand',false,NULL,NULL),
	 ('SGP',222,true,'{"dataset_title": "Singaore", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_sgp", "dataset_locations": ["sgp"]}','raw_ondemand',false,NULL,NULL),
	 ('SDN',140,true,'{"dataset_title": "Sudan", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_sdn", "dataset_locations": ["sdn"]}','raw_ondemand',false,NULL,NULL),
	 ('SUR',88,true,'{"dataset_title": "Suriname", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_sur", "dataset_locations": ["sur"]}','raw_ondemand',false,NULL,NULL),
	 ('SEN',234,true,'{"dataset_title": "Senegal", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_sen", "dataset_locations": ["sen"]}','raw_ondemand',false,NULL,NULL),
	 ('SSD',122,true,'{"dataset_title": "South Sudan", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_ssd", "dataset_locations": ["ssd"]}','raw_ondemand',false,NULL,NULL),
	 ('ESP',5,true,'{"dataset_title": "Spain", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_esp", "dataset_locations": ["esp"]}','raw_ondemand',false,NULL,NULL),
	 ('LKA',130,true,'{"dataset_title": "Sri Lanka", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_lka", "dataset_locations": ["lka"]}','raw_ondemand',false,NULL,NULL),
	 ('SRB',218,true,'{"dataset_title": "Serbia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_srb", "dataset_locations": ["srb"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('SYC',219,true,'{"dataset_title": "Seychelles", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_syc", "dataset_locations": ["syc"]}','raw_ondemand',false,NULL,NULL),
	 ('SVK',220,true,'{"dataset_title": "Slovakia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_svk", "dataset_locations": ["svk"]}','raw_ondemand',false,NULL,NULL),
	 ('SVN',137,true,'{"dataset_title": "Slovenia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_svn", "dataset_locations": ["svn"]}','raw_ondemand',false,NULL,NULL),
	 ('SLB',139,true,'{"dataset_title": "Solomon Islands", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_slb", "dataset_locations": ["slb"]}','raw_ondemand',false,NULL,NULL),
	 ('SOM',112,true,'{"dataset_title": "Somalia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_som", "dataset_locations": ["som"]}','raw_ondemand',false,NULL,NULL),
	 ('ZAF',223,true,'{"dataset_title": "South Africa", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_zaf", "dataset_locations": ["zaf"]}','raw_ondemand',false,NULL,NULL),
	 ('SGS',110,true,'{"dataset_title": "South Georgia and the South Sandwich Islands", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_sgs", "dataset_locations": ["sgs"]}','raw_ondemand',false,NULL,NULL),
	 ('KOR',136,true,'{"dataset_title": "South Korea", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_kor", "dataset_locations": ["kor"]}','raw_ondemand',false,NULL,NULL),
	 ('SJM',111,true,'{"dataset_title": "Svalbard and Jan Mayen Islands", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_sjm", "dataset_locations": ["sjm"]}','raw_ondemand',false,NULL,NULL),
	 ('SWE',124,true,'{"dataset_title": "Sweden", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_swe", "dataset_locations": ["swe"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('CHE',21,true,'{"dataset_title": "Switzerland", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_che", "dataset_locations": ["che"]}','raw_ondemand',false,NULL,NULL),
	 ('TUN',102,true,'{"dataset_title": "Tunisia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_tun", "dataset_locations": ["tun"]}','raw_ondemand',false,NULL,NULL),
	 ('SYR',237,true,'{"dataset_title": "Syria", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_syr", "dataset_locations": ["syr"]}','raw_ondemand',false,NULL,NULL),
	 ('TWN',36,true,'{"dataset_title": "Taiwan", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_twn", "dataset_locations": ["twn"]}','raw_ondemand',false,NULL,NULL),
	 ('TGO',146,true,'{"dataset_title": "Togo", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_tgo", "dataset_locations": ["tgo"]}','raw_ondemand',false,NULL,NULL),
	 ('TKL',35,true,'{"dataset_title": "Tokelau", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_tkl", "dataset_locations": ["tkl"]}','raw_ondemand',false,NULL,NULL),
	 ('TJK',231,true,'{"dataset_title": "Tajikistan", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_tjk", "dataset_locations": ["tjk"]}','raw_ondemand',false,NULL,NULL),
	 ('TZA',145,true,'{"dataset_title": "Tanzania", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_tza", "dataset_locations": ["tza"]}','raw_ondemand',false,NULL,NULL),
	 ('THA',20,true,'{"dataset_title": "Thailand", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_tha", "dataset_locations": ["tha"]}','raw_ondemand',false,NULL,NULL),
	 ('TLS',96,true,'{"dataset_title": "Timor-Leste", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_tls", "dataset_locations": ["tls"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('TUR',163,true,'{"dataset_title": "Turkey", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_tur", "dataset_locations": ["tur"]}','raw_ondemand',false,NULL,NULL),
	 ('TKM',147,true,'{"dataset_title": "Turkmenistan", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_tkm", "dataset_locations": ["tjk"]}','raw_ondemand',false,NULL,NULL),
	 ('TCA',85,true,'{"dataset_title": "Turks and Caicos Islands", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_tca", "dataset_locations": ["tca"]}','raw_ondemand',false,NULL,NULL),
	 ('TUV',216,true,'{"dataset_title": "Tuvalu", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_tuv", "dataset_locations": ["tuv"]}','raw_ondemand',false,NULL,NULL),
	 ('URY',160,true,'{"dataset_title": "Uruguay", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_ury", "dataset_locations": ["ury"]}','raw_ondemand',false,NULL,NULL),
	 ('UGA',162,true,'{"dataset_title": "Uganda", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_uga", "dataset_locations": ["uga"]}','raw_ondemand',false,NULL,NULL),
	 ('UKR',132,true,'{"dataset_title": "Ukraine", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_ukr", "dataset_locations": ["ukr"]}','raw_ondemand',false,NULL,NULL),
	 ('ARE',224,true,'{"dataset_title": "United Arab Emirates", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_are", "dataset_locations": ["are"]}','raw_ondemand',false,NULL,NULL),
	 ('GBR',80,true,'{"dataset_title": "United Kingdom", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_gbr", "dataset_locations": ["gbr"]}','raw_ondemand',false,NULL,NULL),
	 ('USA',235,true,'{"dataset_title": "United States", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_usa", "dataset_locations": ["usa"]}','raw_ondemand',false,NULL,NULL);
INSERT INTO public.hdx (iso3,cid,hdx_upload,dataset,queue,meta,categories,geometry) VALUES
	 ('VIR',113,true,'{"dataset_title": "United States Virgin Islands", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_vir", "dataset_locations": ["vir"]}','raw_ondemand',false,NULL,NULL),
	 ('UZB',232,true,'{"dataset_title": "Uzbekistan", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_uzb", "dataset_locations": ["uzb"]}','raw_ondemand',false,NULL,NULL),
	 ('VUT',25,true,'{"dataset_title": "Vanuatu", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_vut", "dataset_locations": ["vut"]}','raw_ondemand',false,NULL,NULL),
	 ('VEN',193,true,'{"dataset_title": "Venezuela", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_ven", "dataset_locations": ["ven"]}','raw_ondemand',false,NULL,NULL),
	 ('VNM',205,true,'{"dataset_title": "Viet Nam", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_vnm", "dataset_locations": ["vnm"]}','raw_ondemand',false,NULL,NULL),
	 ('WLF',143,true,'{"dataset_title": "Wallis and Futuna Islands", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_wlf", "dataset_locations": ["wlf"]}','raw_ondemand',false,NULL,NULL),
	 ('YEM',135,true,'{"dataset_title": "Yemen", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_yem", "dataset_locations": ["yem"]}','raw_ondemand',false,NULL,NULL),
	 ('ZMB',184,true,'{"dataset_title": "Zambia", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_zmb", "dataset_locations": ["zmb"]}','raw_ondemand',false,NULL,NULL),
	 ('ZWE',190,true,'{"dataset_title": "Zimbabwe", "dataset_folder": "ISO3", "update_frequency": "monthly", "dataset_prefix": "hotosm_zwe", "dataset_locations": ["zwe"]}','raw_ondemand',false,NULL,NULL);

CREATE UNIQUE INDEX if not exists unique_dataset_prefix_idx ON public.hdx ((dataset->>'dataset_prefix'));
