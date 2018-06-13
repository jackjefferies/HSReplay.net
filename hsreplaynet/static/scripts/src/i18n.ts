import i18n, { InitOptions } from "i18next";
import { unset } from "lodash";
import CustomCallbackBackend from "i18next-callback-backend";
import ICU from "i18next-icu";
import de from "i18next-icu/locale-data/de";
import en from "i18next-icu/locale-data/en";
import es from "i18next-icu/locale-data/es";
import fr from "i18next-icu/locale-data/fr";
import it from "i18next-icu/locale-data/it";
import ja from "i18next-icu/locale-data/ja";
import ko from "i18next-icu/locale-data/ko";
import pl from "i18next-icu/locale-data/pl";
import pt from "i18next-icu/locale-data/pt";
import ru from "i18next-icu/locale-data/ru";
import th from "i18next-icu/locale-data/th";
import zh from "i18next-icu/locale-data/zh";
import UserData from "./UserData";

export const I18N_NAMESPACE_FRONTEND = "frontend";
export const I18N_NAMESPACE_HEARTHSTONE = "hearthstone";

// just used while we feature flag frontend translations
UserData.create();

// create icu as instance so we can clear memoization cache (see below)
const icu = new ICU();

i18n
	.use(CustomCallbackBackend)
	.use(icu)
	.init({
		// keys as strings
		defaultNS: I18N_NAMESPACE_FRONTEND,
		fallbackNS: false,
		fallbackLng: false,
		keySeparator: false,
		lowerCaseLng: true,
		nsSeparator: false,

		// initial namespaces to load
		ns: ["frontend", "hearthstone"],

		// i18next-icu
		i18nFormat: {
			/* We cannot load these dynamically right now due to the different
			file names. There's not a lot data behind these though, so we just
			hardcode the languages we support for now. */
			localeData: [de, en, es, fr, it, ja, ko, pl, pt, ru, th, zh],
		},

		// not required using i18next-react
		interpolation: {
			escapeValue: false,
		},

		// CustomCallbackBackend
		customLoad: async (language, namespace, callback) => {
			const translations = {};
			if (namespace === "translation") {
				// default fallback namespace, do not load
				callback(null, translations);
				return;
			}
			if (namespace === I18N_NAMESPACE_HEARTHSTONE) {
				try {
					/* By specifying the same webpackChunkName, all the files for one language are
				merged into a single module. This results in one network request per language */
					const modules = await Promise.all([
						import(/* webpackChunkName: "i18n/[index]" */ `i18n/${language}/hearthstone/global.json`),
						import(/* webpackChunkName: "i18n/[index]" */ `i18n/${language}/hearthstone/gameplay.json`),
						import(/* webpackChunkName: "i18n/[index]" */ `i18n/${language}/hearthstone/presence.json`),
					]);
					for (const module of modules) {
						if (!module) {
							continue;
						}
						Object.assign(translations, module);
					}
				} catch (e) {
					console.error(e);
				}
			} else if (
				namespace === I18N_NAMESPACE_FRONTEND &&
				UserData.hasFeature("frontend-translations")
			) {
				try {
					Object.assign(
						translations,
						await import(/* webpackChunkName: "i18n/[index]" */ `i18n/${language}/frontend.json`),
					);
				} catch (e) {
					console.error(e);
				}
			}
			if (Object.keys(translations).length !== 0) {
				// reset memoization until https://github.com/i18next/i18next-icu/issues/3 is fixed
				unset(icu.mem, `${language}.${namespace}`);
			}
			// pass translations to i18next
			callback(null, translations);
		},
	} as InitOptions);

export default i18n;
