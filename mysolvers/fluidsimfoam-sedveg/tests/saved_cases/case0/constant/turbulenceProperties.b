FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "constant";
    object      turbulenceProperties;
}

simulationType    RAS;

RAS
{
    RASModel       twophasekOmegaVeg;
    turbulence     on;
    printCoeffs    on;
    twophasekOmegaVegCoeffs
    {
        alphaOmega         0.52;
        betaOmega          0.072;
        C3om               0.35;
        C4om               1.0;
        alphaKomega        0.5;
        alphaOmegaOmega    0.5;
        Clim               0.0;
        sigmad             0.0;
        Cmu                0.09;
        KE2                0.0;
        KE4                1.0;
        KE6                0.2;
        KE7                0.15;
        nutMax             0.005;
        popeCorrection     false;
        writeTke           true;
    }
    twophaseMixingLengthCoeffs
    {
        expoLM        1.0;
        alphaMaxLM    0.55;
        kappaLM       0.225;
        Cmu           0.09;
        nutMax        0.005;
    }
    twophasekEpsilonCoeffs
    {
        C1          1.44;
        C2          1.92;
        C3ep        1.2;
        C4ep        1;
        alphak      1.0;
        alphaEps    1.3;
        Cmu         0.09;
        KE2         0.0;
        KE4         1.0;
        nutMax      0.005;
    }
}
