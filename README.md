<div align="center">
  <img src="./docs/logo.svg" width="200"/>
  <h1>spectrumSense</h1>
  <p>Generate ICC profiles based off of specrtometer readings.</p>
  
</div>


## 📙 API Documentation

<h1>⚠️ You are reading the docs for the <a href="https://github.com/Nfloc/SpectrumSense/tree/main">main</a> branch ⚠️</h1>

Please proceed to the [RELEASES](https://github.com/Nfloc/spectrumSense/releases) for the **stable** release of SpectrumSense.

---

## 🚀 Features

- 🟥 Patch Calibration - Create your own color baselines to compare against your monitor!
- 🟧 Monitor Calibration - Generate monitor color data via spectral components!
- 🟨 CIEXYZ - Turn raw spectrometer data into readable XYZ values!
- 🟩 ICC Profiles - Create ICC profiles for your monitor based on user calibration.
- 🟦 TBD!
- 🟪 TBD!

> **Note**: spectrumSense tries to generate realistic data based off of the Macbeth ColorChecker under D65 illumination;
> To get maximum percision create you own baselines that reflect your enviorments and requirements.

## 📦 Install
### All Dependencies

- ArgyllCMS
- pyside6
- pyserial
- json
- colour-science
- scipy
- numpy
- datetime
- Pillow

To install all dependencies navigate to
*spectrumSense -> scripts -> install_all.bat*
and run install_all.bat

To run the program please run ***spectrumSense.bat***

## 🤝 Sponsors

SpectrumSense is an MIT-licensed open source project with its ongoing development made possible entirely by the support of these awesome backers

### Sponsors

Me

### Backers

Also Me

## ✨ Contributing

Please make sure to read the [Contributing Guide]() before making a pull request.

## 📘 Credits

## 📝 Changelog

Detailed changes for each release are documented in the [release notes]().

## 🔑 License

[MIT](https://github.com/Nfloc/SpectrumSense/blob/main/LICENSE)
